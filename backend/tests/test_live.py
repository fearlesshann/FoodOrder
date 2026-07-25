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
                upload_dir=tmp_path / "uploads",
            )
        )
    )


def test_websocket_receives_selection_and_note_events(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    dish = client.get("/api/catalog").json()[0]

    with client.websocket_connect("/api/menu/live") as socket:
        assert socket.receive_json() == {"type": "connected"}

        selected = client.post(f"/api/menu/selections/{dish['id']}").json()
        created = socket.receive_json()
        assert created["type"] == "selection.created"
        assert created["selection"]["dish"]["name"] == "红烧肉"

        client.patch(f"/api/menu/selections/{selected['id']}", json={"note": "不要葱"})
        updated = socket.receive_json()
        assert updated["type"] == "selection.updated"
        assert updated["selection"]["note"] == "不要葱"

        client.delete(f"/api/menu/selections/{selected['id']}")
        assert socket.receive_json() == {"type": "selection.deleted", "selection_id": selected["id"]}
