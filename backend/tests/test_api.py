from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        allowed_origins=("http://localhost:5173",),
    )
    return TestClient(create_app(settings))


def test_dish_crud_and_family_isolation(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    created = client.post(
        "/api/menus/family-a/dishes",
        json={"name": "  红烧肉  ", "ordered_by": " 小明 "},
    )
    assert created.status_code == 201
    dish = created.json()
    assert dish["name"] == "红烧肉"
    assert dish["ordered_by"] == "小明"

    menu = client.get("/api/menus/family-a/today")
    assert menu.status_code == 200
    assert [item["name"] for item in menu.json()["dishes"]] == ["红烧肉"]

    other_menu = client.get("/api/menus/family-b/today")
    assert other_menu.json()["dishes"] == []

    updated = client.patch(
        f"/api/menus/family-a/dishes/{dish['id']}", json={"name": "糖醋排骨"}
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "糖醋排骨"

    hidden = client.patch(
        f"/api/menus/family-b/dishes/{dish['id']}", json={"name": "不应成功"}
    )
    assert hidden.status_code == 404

    deleted = client.delete(f"/api/menus/family-a/dishes/{dish['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/menus/family-a/today").json()["dishes"] == []


def test_rejects_invalid_names_and_family_codes(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    blank = client.post(
        "/api/menus/family-a/dishes", json={"name": "   ", "ordered_by": "小明"}
    )
    assert blank.status_code == 422

    too_long = client.post(
        "/api/menus/family-a/dishes",
        json={"name": "菜" * 41, "ordered_by": "小明"},
    )
    assert too_long.status_code == 422

    invalid_code = client.get("/api/menus/!!bad!!/today")
    assert invalid_code.status_code == 422


def test_cors_only_allows_configured_origin(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.options(
        "/api/menus/family-a/today",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
