from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from . import models  # noqa: F401
from .models import CatalogDish, Category
from .api import router
from .config import Settings, load_settings
from .database import Database
from .live import LiveMenuHub


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or load_settings()
    app = FastAPI(title="今晚吃什么 API", version="0.1.0")
    app.state.database = Database(resolved.database_url)
    app.state.settings = resolved
    app.state.live = LiveMenuHub()
    app.state.database.create_all()
    app.state.database.migrate_catalog_category()
    resolved.upload_dir.mkdir(parents=True, exist_ok=True)

    with app.state.database.session_factory() as session:
        category_by_name = {item.name: item for item in session.scalars(select(Category)).all()}
        for order, name in enumerate(("荤菜", "素菜", "汤品"), start=1):
            if name not in category_by_name:
                category = Category(name=name, sort_order=order)
                session.add(category)
                session.flush()
                category_by_name[name] = category
        if session.scalar(select(CatalogDish.id).limit(1)) is None:
            session.add_all(
                [
                    CatalogDish(name="红烧肉", image_url="/dishes/hong-shao-rou.webp", category_id=category_by_name["荤菜"].id, sort_order=1),
                    CatalogDish(name="清蒸鲈鱼", image_url="/dishes/qing-zheng-lu-yu.webp", category_id=category_by_name["荤菜"].id, sort_order=2),
                    CatalogDish(name="蒜蓉生菜", image_url="/dishes/suan-rong-sheng-cai.webp", category_id=category_by_name["素菜"].id, sort_order=3),
                ]
            )
            session.commit()
        else:
            default_assets = {
                "红烧肉": "/dishes/hong-shao-rou.webp",
                "清蒸鲈鱼": "/dishes/qing-zheng-lu-yu.webp",
                "蒜蓉生菜": "/dishes/suan-rong-sheng-cai.webp",
            }
            changed = False
            for dish in session.scalars(select(CatalogDish).where(CatalogDish.name.in_(default_assets))):
                if dish.image_filename is None and dish.image_url != default_assets[dish.name]:
                    dish.image_url = default_assets[dish.name]
                    changed = True
                if dish.category_id is None:
                    dish.category_id = category_by_name["素菜" if dish.name == "蒜蓉生菜" else "荤菜"].id
                    changed = True
            if changed:
                session.commit()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router)
    app.mount("/uploads", StaticFiles(directory=resolved.upload_dir), name="uploads")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
