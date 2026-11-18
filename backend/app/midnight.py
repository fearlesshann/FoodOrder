from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from .database import Database
from .live import MENU_SPACE, LiveMenuHub
from .models import Selection

logger = logging.getLogger(__name__)

SHANGHAI = ZoneInfo("Asia/Shanghai")
Now = Callable[[], datetime]
Sleep = Callable[[float], Awaitable[None]]


def shanghai_now() -> datetime:
    return datetime.now(SHANGHAI)


def _in_shanghai(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ValueError("需要带时区的时间")
    return moment.astimezone(SHANGHAI)


def today_shanghai(moment: datetime | None = None) -> date:
    current = shanghai_now() if moment is None else _in_shanghai(moment)
    return current.date()


def next_midnight(moment: datetime | None = None) -> datetime:
    current = shanghai_now() if moment is None else _in_shanghai(moment)
    return datetime.combine(current.date() + timedelta(days=1), time.min, tzinfo=SHANGHAI)


def seconds_until_next_midnight(moment: datetime | None = None) -> float:
    current = shanghai_now() if moment is None else _in_shanghai(moment)
    return (next_midnight(current) - current).total_seconds()


def delete_expired_selections(database: Database, today: date) -> list[int]:
    with database.session_factory() as session:
        rows = list(
            session.scalars(
                select(Selection).where(Selection.dinner_date < today).order_by(Selection.id)
            ).all()
        )
        if not rows:
            return []
        ids = [row.id for row in rows]
        for row in rows:
            session.delete(row)
        session.commit()
        return ids


async def clear_expired_selections(database: Database, live: LiveMenuHub, today: date) -> list[int]:
    """Drop selections from before this Shanghai date and tell connected clients."""
    ids = delete_expired_selections(database, today)
    await live.broadcast(
        MENU_SPACE,
        {"type": "selections.cleared", "selection_ids": ids, "dinner_date": today.isoformat()},
    )
    for selection_id in ids:
        await live.broadcast(MENU_SPACE, {"type": "selection.deleted", "selection_id": selection_id})
    return ids


async def midnight_clear_loop(
    database: Database,
    live: LiveMenuHub,
    *,
    now: Now = shanghai_now,
    sleep: Sleep = asyncio.sleep,
    ready: asyncio.Event | None = None,
) -> None:
    """Clear expired picks immediately, then at every later Asia/Shanghai midnight.

    The first pass covers a process that comes up after midnight. The following
    wait is always the next Shanghai midnight, so a start just before midnight
    does not skip the rollover or treat UTC midnight as the boundary.
    """
    announced = False
    while True:
        today = today_shanghai(now())
        removed = 0
        try:
            removed = len(await clear_expired_selections(database, live, today))
        except Exception:
            logger.exception("上海时区午夜清空已点失败")
        else:
            logger.info(
                "已点清空检查完成：Asia/Shanghai %s，删除 %s 条，下一次 %s",
                today.isoformat(),
                removed,
                next_midnight(now()).isoformat(timespec="seconds"),
            )
        finally:
            if ready is not None and not announced:
                ready.set()
                announced = True
        delay = seconds_until_next_midnight(now())
        await sleep(delay if delay > 0 else 1.0)
