from __future__ import annotations

import io
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path as ApiPath, Request, UploadFile, WebSocket, WebSocketDisconnect, status
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import CatalogDish, Category, Selection
from .schemas import CatalogDishRead, CategoryRead, CategoryWrite, MenuRead, SelectionNoteUpdate, SelectionRead


router = APIRouter(prefix="/api", tags=["dinner"])
MENU_SPACE = "home-menu"
MAX_IMAGE_BYTES = 20 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
register_heif_opener()


def get_session(request: Request):
    yield from request.app.state.database.session()


def clean_name(name: str) -> str:
    value = name.strip()
    if not 1 <= len(value) <= 40:
        raise HTTPException(status_code=422, detail="菜名需为 1–40 个字符")
    return value


async def save_image(upload: UploadFile, upload_dir: Path) -> tuple[str, str]:
    suffix = Path(upload.filename or "").suffix.lower()
    if upload.content_type not in ALLOWED_IMAGE_TYPES and suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise HTTPException(status_code=422, detail="图片仅支持 JPEG、PNG、WebP、HEIC 或 HEIF")
    content = await upload.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="图片不能超过 20MB")
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(content))).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=422, detail="图片文件无效") from exc

    image.thumbnail((1920, 1280))
    filename = f"{uuid.uuid4().hex}.webp"
    upload_dir.mkdir(parents=True, exist_ok=True)
    image.save(upload_dir / filename, "WEBP", quality=86, method=6)
    return f"/uploads/{filename}", filename


def remove_uploaded_image(upload_dir: Path, filename: str | None) -> None:
    if not filename:
        return
    path = upload_dir / filename
    if path.is_file():
        path.unlink()


def selection_payload(selection: Selection) -> dict:
    return SelectionRead.model_validate(selection).model_dump(mode="json")


@router.get("/catalog", response_model=list[CatalogDishRead])
def get_catalog(session: Session = Depends(get_session)) -> list[CatalogDish]:
    return list(session.scalars(select(CatalogDish).order_by(CatalogDish.sort_order, CatalogDish.id)).all())


@router.get("/admin/categories", response_model=list[CategoryRead])
def get_categories(session: Session = Depends(get_session)) -> list[Category]:
    return list(session.scalars(select(Category).order_by(Category.sort_order, Category.id)).all())


@router.post("/admin/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request,
    payload: CategoryWrite,
    session: Session = Depends(get_session),
) -> Category:
    next_order = session.scalar(select(func.coalesce(func.max(Category.sort_order), 0))) or 0
    category = Category(name=payload.name, sort_order=next_order + 1)
    session.add(category)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="这个分类已经存在") from exc
    session.refresh(category)
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "catalog.changed"})
    return category


@router.patch("/admin/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    request: Request,
    payload: CategoryWrite,
    category_id: int = ApiPath(gt=0),
    session: Session = Depends(get_session),
) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="没有找到这个分类")
    category.name = payload.name
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="这个分类已经存在") from exc
    session.refresh(category)
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "catalog.changed"})
    return category


@router.delete("/admin/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    request: Request,
    category_id: int = ApiPath(gt=0),
    session: Session = Depends(get_session),
) -> None:
    category = session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="没有找到这个分类")
    if session.scalar(select(CatalogDish.id).where(CatalogDish.category_id == category_id).limit(1)) is not None:
        raise HTTPException(status_code=409, detail="这个分类下还有菜品，不能删除")
    session.delete(category)
    session.commit()
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "catalog.changed"})


@router.post("/admin/dishes", response_model=CatalogDishRead, status_code=status.HTTP_201_CREATED)
async def create_catalog_dish(
    request: Request,
    name: str = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> CatalogDish:
    value = clean_name(name)
    if session.get(Category, category_id) is None:
        raise HTTPException(status_code=422, detail="请选择有效分类")
    image_url, filename = await save_image(image, request.app.state.settings.upload_dir)
    next_order = session.scalar(select(func.coalesce(func.max(CatalogDish.sort_order), 0))) or 0
    dish = CatalogDish(name=value, image_url=image_url, image_filename=filename, category_id=category_id, sort_order=next_order + 1)
    session.add(dish)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        remove_uploaded_image(request.app.state.settings.upload_dir, filename)
        raise HTTPException(status_code=409, detail="这个菜名已经存在") from exc
    session.refresh(dish)
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "catalog.changed"})
    return dish


@router.patch("/admin/dishes/{dish_id}", response_model=CatalogDishRead)
async def update_catalog_dish(
    request: Request,
    dish_id: int = ApiPath(gt=0),
    name: str = Form(...),
    category_id: int = Form(...),
    image: UploadFile | None = File(default=None),
    session: Session = Depends(get_session),
) -> CatalogDish:
    dish = session.get(CatalogDish, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="没有找到这道菜")
    value = clean_name(name)
    if session.get(Category, category_id) is None:
        raise HTTPException(status_code=422, detail="请选择有效分类")
    old_filename = dish.image_filename
    new_filename: str | None = None
    if image is not None:
        dish.image_url, new_filename = await save_image(image, request.app.state.settings.upload_dir)
        dish.image_filename = new_filename
    dish.name = value
    dish.category_id = category_id
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        remove_uploaded_image(request.app.state.settings.upload_dir, new_filename)
        raise HTTPException(status_code=409, detail="这个菜名已经存在") from exc
    session.refresh(dish)
    if new_filename:
        remove_uploaded_image(request.app.state.settings.upload_dir, old_filename)
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "catalog.changed"})
    return dish


@router.delete("/admin/dishes/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_dish(
    request: Request,
    dish_id: int = ApiPath(gt=0),
    session: Session = Depends(get_session),
) -> None:
    dish = session.get(CatalogDish, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="没有找到这道菜")
    has_selection = session.scalar(select(Selection.id).where(Selection.dish_id == dish_id).limit(1))
    if has_selection is not None:
        raise HTTPException(status_code=409, detail="这道菜已在菜单记录中，暂时不能删除")
    filename = dish.image_filename
    session.delete(dish)
    session.commit()
    remove_uploaded_image(request.app.state.settings.upload_dir, filename)
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "catalog.changed"})


@router.get("/menu/today", response_model=MenuRead)
def get_today_menu(session: Session = Depends(get_session)) -> MenuRead:
    today = date.today()
    selections = session.scalars(
        select(Selection).where(Selection.dinner_date == today).order_by(Selection.created_at, Selection.id)
    ).unique().all()
    return MenuRead(dinner_date=today, selections=list(selections))


@router.post("/menu/selections/{dish_id}", response_model=SelectionRead, status_code=status.HTTP_201_CREATED)
async def select_dish(
    request: Request,
    dish_id: int = ApiPath(gt=0),
    session: Session = Depends(get_session),
) -> Selection:
    if session.get(CatalogDish, dish_id) is None:
        raise HTTPException(status_code=404, detail="没有找到这道菜")
    selection = Selection(dish_id=dish_id, dinner_date=date.today(), note="")
    session.add(selection)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        existing = session.scalar(
            select(Selection).where(Selection.dish_id == dish_id, Selection.dinner_date == date.today())
        )
        if existing:
            return existing
        raise HTTPException(status_code=409, detail="这道菜已经选过了") from exc
    session.refresh(selection)
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "selection.created", "selection": selection_payload(selection)})
    return selection


@router.patch("/menu/selections/{selection_id}", response_model=SelectionRead)
async def update_selection_note(
    request: Request,
    payload: SelectionNoteUpdate,
    selection_id: int = ApiPath(gt=0),
    session: Session = Depends(get_session),
) -> Selection:
    selection = session.get(Selection, selection_id)
    if selection is None or selection.dinner_date != date.today():
        raise HTTPException(status_code=404, detail="没有找到这条点菜记录")
    selection.note = payload.note
    session.commit()
    session.refresh(selection)
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "selection.updated", "selection": selection_payload(selection)})
    return selection


@router.delete("/menu/selections/{selection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unselect_dish(
    request: Request,
    selection_id: int = ApiPath(gt=0),
    session: Session = Depends(get_session),
) -> None:
    selection = session.get(Selection, selection_id)
    if selection is None or selection.dinner_date != date.today():
        raise HTTPException(status_code=404, detail="没有找到这条点菜记录")
    session.delete(selection)
    session.commit()
    await request.app.state.live.broadcast(MENU_SPACE, {"type": "selection.deleted", "selection_id": selection_id})


@router.websocket("/menu/live")
async def live_menu(websocket: WebSocket) -> None:
    hub = websocket.app.state.live
    await hub.connect(MENU_SPACE, websocket)
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(MENU_SPACE, websocket)
