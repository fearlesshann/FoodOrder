from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class LiveMenuHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, family_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[family_code].add(websocket)

    def disconnect(self, family_code: str, websocket: WebSocket) -> None:
        connections = self._connections.get(family_code)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(family_code, None)

    async def broadcast(self, family_code: str, message: dict) -> None:
        stale: list[WebSocket] = []
        for websocket in tuple(self._connections.get(family_code, set())):
            try:
                await websocket.send_json(message)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(family_code, websocket)

