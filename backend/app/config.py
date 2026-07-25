from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    allowed_origins: tuple[str, ...]
    upload_dir: Path = Path("./uploads")


def load_settings() -> Settings:
    origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./dinner.db"),
        allowed_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
        upload_dir=Path(os.getenv("UPLOAD_DIR", "./uploads")),
    )
