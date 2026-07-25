from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                database_url=f"sqlite:///{tmp_path / 'live.db'}",
                allowed_origins=("http://localhost:5173",),
            )
        )
    )


def test_websocket_receives_crud_events(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    with client.websocket_connect("/api/menus/family-a/live") as socket:
        assert socket.receive_json() == {"type": "connected"}

        created = client.post(
            "/api/menus/family-a/dishes",
            json={"name": "番茄炒蛋", "ordered_by": "妈妈"},
        ).json()
        event = socket.receive_json()
        assert event["type"] == "dish.created"
        assert event["dish"]["name"] == "番茄炒蛋"

        client.patch(
            f"/api/menus/family-a/dishes/{created['id']}",
            json={"name": "番茄鸡蛋"},
        )
        assert socket.receive_json()["type"] == "dish.updated"

        client.delete(f"/api/menus/family-a/dishes/{created['id']}")
        assert socket.receive_json() == {"type": "dish.deleted", "dish_id": created["id"]}


def test_websocket_isolated_by_family(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    with client.websocket_connect("/api/menus/family-a/live") as socket:
        socket.receive_json()
        client.post(
            "/api/menus/family-b/dishes",
            json={"name": "排骨汤", "ordered_by": "爸爸"},
        )
        client.post(
            "/api/menus/family-a/dishes",
            json={"name": "青菜", "ordered_by": "小明"},
        )
        event = socket.receive_json()
        assert event["dish"]["name"] == "青菜"
