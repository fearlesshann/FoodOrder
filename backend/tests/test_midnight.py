from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.live import LiveMenuHub
from app.main import create_app
from app.midnight import (
    clear_expired_selections,
    midnight_clear_loop,
    next_midnight,
    seconds_until_next_midnight,
    today_shanghai,
)
from app.models import CatalogDish, Category, Selection

UTC = ZoneInfo("UTC")
SHANGHAI = ZoneInfo("Asia/Shanghai")


def make_app(tmp_path: Path, *, midnight_clear: bool = False):
    return create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'midnight.db'}",
            allowed_origins=("http://localhost:5173",),
            upload_dir=tmp_path / "uploads",
            midnight_clear=midnight_clear,
        )
    )


def add_selection(app, dinner_date: date, dish_index: int, note: str = "") -> int:
    with app.state.database.session_factory() as session:
        dish = session.scalars(select(CatalogDish).order_by(CatalogDish.id)).all()[dish_index]
        selection = Selection(dish_id=dish.id, dinner_date=dinner_date, note=note)
        session.add(selection)
        session.commit()
        return selection.id


def selection_ids(app) -> list[int]:
    with app.state.database.session_factory() as session:
        return list(session.scalars(select(Selection.id).order_by(Selection.id)).all())


class RecordingLive(LiveMenuHub):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[dict] = []

    async def broadcast(self, family_code: str, message: dict) -> None:
        self.messages.append(message)
        await super().broadcast(family_code, message)


def test_shanghai_midnight_is_not_utc_and_has_no_dst() -> None:
    assert today_shanghai(datetime(2026, 11, 18, 15, 59, tzinfo=UTC)) == date(2026, 11, 18)
    assert today_shanghai(datetime(2026, 11, 18, 16, 0, tzinfo=UTC)) == date(2026, 11, 19)
    # 00:00 UTC is 08:00 in Suzhou, still the same dinner day.
    assert today_shanghai(datetime(2026, 11, 18, 0, 0, tzinfo=UTC)) == date(2026, 11, 18)
    assert seconds_until_next_midnight(datetime(2026, 11, 18, 0, 30, tzinfo=UTC)) == pytest.approx(15.5 * 3600)

    before = datetime(2026, 11, 18, 23, 59, 30, tzinfo=SHANGHAI)
    assert next_midnight(before) == datetime(2026, 11, 19, 0, 0, tzinfo=SHANGHAI)
    assert seconds_until_next_midnight(before) == 30
    at_midnight = datetime(2026, 11, 19, 0, 0, tzinfo=SHANGHAI)
    assert next_midnight(at_midnight) == datetime(2026, 11, 20, 0, 0, tzinfo=SHANGHAI)
    assert seconds_until_next_midnight(at_midnight) == 86400

    summer = datetime(2026, 7, 15, 12, tzinfo=SHANGHAI)
    winter = datetime(2026, 1, 15, 12, tzinfo=SHANGHAI)
    assert summer.utcoffset() == winter.utcoffset() == timedelta(hours=8)
    assert summer.dst() == winter.dst() == timedelta(0)


def test_timezone_data_is_installed_with_the_backend() -> None:
    project = Path(__file__).parents[1] / "pyproject.toml"
    assert "tzdata" in project.read_text(encoding="utf-8")


def test_clear_removes_only_previous_shanghai_dates_and_broadcasts(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    # 20:00 UTC is 04:00 the next day in Shanghai. UTC has not rolled, Shanghai has.
    moment = datetime(2026, 11, 18, 20, 0, tzinfo=UTC)
    assert today_shanghai(moment) == date(2026, 11, 19)
    kept = add_selection(app, date(2026, 11, 19), 0, note="今晚")
    expired = add_selection(app, date(2026, 11, 18), 1, note="昨晚")
    hub = RecordingLive()

    with app.state.database.session_factory() as session:
        dishes = session.scalar(select(func.count()).select_from(CatalogDish))
        categories = session.scalar(select(func.count()).select_from(Category))

    cleared = asyncio.run(clear_expired_selections(app.state.database, hub, today_shanghai(moment)))

    assert cleared == [expired]
    assert selection_ids(app) == [kept]
    assert hub.messages == [
        {"type": "selections.cleared", "selection_ids": [expired], "dinner_date": "2026-11-19"},
        {"type": "selection.deleted", "selection_id": expired},
    ]
    with app.state.database.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(CatalogDish)) == dishes
        assert session.scalar(select(func.count()).select_from(Category)) == categories
        dish = session.get(CatalogDish, session.scalars(select(CatalogDish.id).order_by(CatalogDish.id)).all()[1])
        assert dish is not None and dish.name == "清蒸鲈鱼"

    hub.messages.clear()
    again = asyncio.run(clear_expired_selections(app.state.database, hub, today_shanghai(moment)))
    assert again == []
    assert hub.messages == [
        {"type": "selections.cleared", "selection_ids": [], "dinner_date": "2026-11-19"},
    ]
    assert selection_ids(app) == [kept]


def test_restart_just_after_midnight_clears_before_waiting_a_full_day(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    expired = add_selection(app, date(2026, 11, 18), 0)
    current = add_selection(app, date(2026, 11, 19), 1)
    moment = datetime(2026, 11, 19, 0, 0, 5, tzinfo=SHANGHAI)
    hub = RecordingLive()
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            midnight_clear_loop(app.state.database, hub, now=lambda: moment, sleep=fake_sleep)
        )

    assert sleeps == [seconds_until_next_midnight(moment)]
    assert sleeps[0] > 23 * 3600
    assert selection_ids(app) == [current]
    assert expired not in selection_ids(app)
    assert hub.messages[0] == {
        "type": "selections.cleared",
        "selection_ids": [expired],
        "dinner_date": "2026-11-19",
    }
    assert {"type": "selection.deleted", "selection_id": expired} in hub.messages


def test_restart_just_before_midnight_keeps_tonight_until_shanghai_rolls(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    tonight = add_selection(app, date(2026, 11, 18), 0, note="今晚")
    upcoming = add_selection(app, date(2026, 11, 19), 1, note="下一顿")
    clock = {"now": datetime(2026, 11, 18, 23, 59, 50, tzinfo=SHANGHAI)}
    hub = RecordingLive()
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)
        if len(sleeps) == 1:
            assert selection_ids(app) == [tonight, upcoming]
            assert hub.messages == [
                {"type": "selections.cleared", "selection_ids": [], "dinner_date": "2026-11-18"},
            ]
            clock["now"] = datetime(2026, 11, 19, 0, 0, 1, tzinfo=SHANGHAI)
            return
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            midnight_clear_loop(
                app.state.database,
                hub,
                now=lambda: clock["now"],
                sleep=fake_sleep,
            )
        )

    assert sleeps[0] == 10
    assert sleeps[1] == seconds_until_next_midnight(clock["now"])
    assert sleeps[1] > 23 * 3600
    assert selection_ids(app) == [upcoming]
    assert hub.messages[-2] == {
        "type": "selections.cleared",
        "selection_ids": [tonight],
        "dinner_date": "2026-11-19",
    }
    assert hub.messages[-1] == {"type": "selection.deleted", "selection_id": tonight}


def test_process_start_clears_previous_day_and_keeps_catalog(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = make_app(tmp_path, midnight_clear=True)
    image = upload_dir / "keep.webp"
    image.write_bytes(b"still-here")
    today = today_shanghai()
    with app.state.database.session_factory() as session:
        dishes = list(session.scalars(select(CatalogDish).order_by(CatalogDish.id)).all())
        dishes[0].image_filename = "keep.webp"
        session.add(Selection(dish_id=dishes[0].id, dinner_date=today - timedelta(days=1), note="昨晚"))
        session.add(Selection(dish_id=dishes[1].id, dinner_date=today, note="今晚"))
        session.commit()
        catalog_count = session.scalar(select(func.count()).select_from(CatalogDish))
        category_count = session.scalar(select(func.count()).select_from(Category))

    with TestClient(app) as client:
        task = app.state.midnight_task
        assert task is not None and not task.done()
        menu = client.get("/api/menu/today").json()
        assert menu["dinner_date"] == today.isoformat()
        assert [item["note"] for item in menu["selections"]] == ["今晚"]
        assert len(client.get("/api/catalog").json()) == catalog_count
        assert len(client.get("/api/admin/categories").json()) == category_count
        assert [dish["name"] for dish in client.get("/api/catalog").json()][:3] == ["红烧肉", "清蒸鲈鱼", "蒜蓉生菜"]
        assert image.read_bytes() == b"still-here"
        with app.state.database.session_factory() as session:
            dish = session.scalars(select(CatalogDish).order_by(CatalogDish.id)).first()
            assert dish is not None and dish.image_filename == "keep.webp"


def test_open_client_receives_clear_without_losing_catalog(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    today = today_shanghai()
    with TestClient(app) as client:
        dishes = client.get("/api/catalog").json()
        first = client.post(f"/api/menu/selections/{dishes[0]['id']}").json()
        second = client.post(f"/api/menu/selections/{dishes[1]['id']}").json()
        current = client.post(f"/api/menu/selections/{dishes[2]['id']}").json()
        with app.state.database.session_factory() as session:
            for selection_id in (first["id"], second["id"]):
                row = session.get(Selection, selection_id)
                assert row is not None
                row.dinner_date = today - timedelta(days=1)
            session.commit()

        with client.websocket_connect("/api/menu/live") as socket:
            assert socket.receive_json() == {"type": "connected", "dinner_date": today.isoformat()}
            cleared_ids = client.portal.call(
                clear_expired_selections,
                app.state.database,
                app.state.live,
                today,
            )
            assert cleared_ids == sorted(cleared_ids)
            messages = [socket.receive_json() for _ in range(1 + len(cleared_ids))]

        assert {first["id"], second["id"]} == set(cleared_ids)
        assert current["id"] not in cleared_ids
        assert messages[0] == {
            "type": "selections.cleared",
            "selection_ids": cleared_ids,
            "dinner_date": today.isoformat(),
        }
        assert messages[1:] == [
            {"type": "selection.deleted", "selection_id": selection_id} for selection_id in cleared_ids
        ]
        menu = client.get("/api/menu/today").json()
        assert [item["id"] for item in menu["selections"]] == [current["id"]]
        again = client.post(f"/api/menu/selections/{dishes[0]['id']}")
        assert again.status_code == 201
        assert again.json()["id"] != first["id"]
        assert [dish["name"] for dish in client.get("/api/catalog").json()] == ["红烧肉", "清蒸鲈鱼", "蒜蓉生菜"]
        assert [item["name"] for item in client.get("/api/admin/categories").json()] == ["荤菜", "素菜", "汤品"]
