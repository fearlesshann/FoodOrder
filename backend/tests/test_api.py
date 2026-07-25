from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        allowed_origins=("http://localhost:5173",),
        upload_dir=tmp_path / "uploads",
    )
    return TestClient(create_app(settings))


def image_file(color: tuple[int, int, int] = (150, 20, 30)) -> tuple[str, io.BytesIO, str]:
    buffer = io.BytesIO()
    Image.new("RGB", (640, 420), color).save(buffer, "PNG")
    buffer.seek(0)
    return ("dish.png", buffer, "image/png")


def test_catalog_starts_with_default_dishes(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.get("/api/catalog")
    assert response.status_code == 200
    assert [dish["name"] for dish in response.json()] == ["红烧肉", "清蒸鲈鱼", "蒜蓉生菜"]
    assert [item["name"] for item in client.get("/api/admin/categories").json()] == ["荤菜", "素菜", "汤品"]
    assert response.json()[0]["category"]["name"] == "荤菜"


def test_category_crud_and_used_category_protection(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    created = client.post("/api/admin/categories", json={"name": "主食"})
    assert created.status_code == 201
    category = created.json()
    renamed = client.patch(f"/api/admin/categories/{category['id']}", json={"name": "面点"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "面点"
    assert client.delete(f"/api/admin/categories/{category['id']}").status_code == 204

    used = client.get("/api/admin/categories").json()[0]
    blocked = client.delete(f"/api/admin/categories/{used['id']}")
    assert blocked.status_code == 409


def test_admin_dish_crud_and_image_validation(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    category = client.get("/api/admin/categories").json()[0]
    created = client.post(
        "/api/admin/dishes",
        data={"name": "糖醋排骨", "category_id": category["id"]},
        files={"image": image_file()},
    )
    assert created.status_code == 201
    dish = created.json()
    assert dish["image_url"].startswith("/uploads/")
    assert len(list((tmp_path / "uploads").glob("*.webp"))) == 1

    updated = client.patch(
        f"/api/admin/dishes/{dish['id']}",
        data={"name": "糖醋小排", "category_id": category["id"]},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "糖醋小排"

    deleted = client.delete(f"/api/admin/dishes/{dish['id']}")
    assert deleted.status_code == 204
    assert list((tmp_path / "uploads").glob("*.webp")) == []

    invalid = client.post(
        "/api/admin/dishes",
        data={"name": "坏图片", "category_id": category["id"]},
        files={"image": ("bad.txt", io.BytesIO(b"not-an-image"), "text/plain")},
    )
    assert invalid.status_code == 422


def test_select_note_unselect_and_prevent_catalog_delete(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    dish = client.get("/api/catalog").json()[0]

    selected = client.post(f"/api/menu/selections/{dish['id']}")
    assert selected.status_code == 201
    selection = selected.json()
    assert selection["dish"]["name"] == "红烧肉"

    duplicate = client.post(f"/api/menu/selections/{dish['id']}")
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == selection["id"]

    noted = client.patch(
        f"/api/menu/selections/{selection['id']}",
        json={"note": "  少辣，不要香菜  "},
    )
    assert noted.status_code == 200
    assert noted.json()["note"] == "少辣，不要香菜"

    menu = client.get("/api/menu/today").json()
    assert len(menu["selections"]) == 1
    assert menu["selections"][0]["note"] == "少辣，不要香菜"

    blocked = client.delete(f"/api/admin/dishes/{dish['id']}")
    assert blocked.status_code == 409

    assert client.delete(f"/api/menu/selections/{selection['id']}").status_code == 204


def test_cors_only_allows_configured_origin(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.options(
        "/api/catalog",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
