from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    allowed_origins: tuple[str, ...]


def load_settings() -> Settings:
    origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./dinner.db"),
        allowed_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
    )

