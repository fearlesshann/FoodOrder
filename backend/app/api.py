from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Dish
from .schemas import DishCreate, DishRead, DishUpdate, MenuRead, validate_family_code


router = APIRouter(prefix="/api/menus", tags=["menus"])


def get_session(request: Request):
    yield from request.app.state.database.session()


FamilyCode = Path(min_length=6, max_length=48)


def checked_family_code(family_code: str) -> str:
    try:
        return validate_family_code(family_code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{family_code}/today", response_model=MenuRead)
def get_today_menu(
    family_code: str = FamilyCode,
    session: Session = Depends(get_session),
) -> MenuRead:
    code = checked_family_code(family_code)
    today = date.today()
    dishes = session.scalars(
        select(Dish)
        .where(Dish.family_code == code, Dish.dinner_date == today)
        .order_by(Dish.created_at, Dish.id)
    ).all()
    return MenuRead(family_code=code, dinner_date=today, dishes=list(dishes))


@router.post("/{family_code}/dishes", response_model=DishRead, status_code=status.HTTP_201_CREATED)
async def create_dish(
    request: Request,
    payload: DishCreate,
    family_code: str = FamilyCode,
    session: Session = Depends(get_session),
) -> Dish:
    code = checked_family_code(family_code)
    dish = Dish(
        family_code=code,
        name=payload.name,
        ordered_by=payload.ordered_by,
        dinner_date=payload.dinner_date or date.today(),
    )
    session.add(dish)
    session.commit()
    session.refresh(dish)
    await request.app.state.live.broadcast(
        code, {"type": "dish.created", "dish": DishRead.model_validate(dish).model_dump(mode="json")}
    )
    return dish


def find_dish(session: Session, family_code: str, dish_id: int) -> Dish:
    dish = session.scalar(
        select(Dish).where(Dish.id == dish_id, Dish.family_code == family_code)
    )
    if dish is None:
        raise HTTPException(status_code=404, detail="没有找到这道菜")
    return dish


@router.patch("/{family_code}/dishes/{dish_id}", response_model=DishRead)
async def update_dish(
    request: Request,
    payload: DishUpdate,
    family_code: str = FamilyCode,
    dish_id: int = Path(gt=0),
    session: Session = Depends(get_session),
) -> Dish:
    code = checked_family_code(family_code)
    dish = find_dish(session, code, dish_id)
    dish.name = payload.name
    session.commit()
    session.refresh(dish)
    await request.app.state.live.broadcast(
        code, {"type": "dish.updated", "dish": DishRead.model_validate(dish).model_dump(mode="json")}
    )
    return dish


@router.delete("/{family_code}/dishes/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish(
    request: Request,
    family_code: str = FamilyCode,
    dish_id: int = Path(gt=0),
    session: Session = Depends(get_session),
) -> None:
    code = checked_family_code(family_code)
    dish = find_dish(session, code, dish_id)
    session.delete(dish)
    session.commit()
    await request.app.state.live.broadcast(code, {"type": "dish.deleted", "dish_id": dish_id})


@router.websocket("/{family_code}/live")
async def live_menu(websocket: WebSocket, family_code: str) -> None:
    try:
        code = validate_family_code(family_code)
    except ValueError:
        await websocket.close(code=1008, reason="无效家庭码")
        return

    hub = websocket.app.state.live
    await hub.connect(code, websocket)
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(code, websocket)
