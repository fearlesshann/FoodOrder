from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, url: str) -> None:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, connect_args=connect_args)
        if url.startswith("sqlite"):
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)

    def migrate_catalog_category(self) -> None:
        if not str(self.engine.url).startswith("sqlite"):
            return
        with self.engine.begin() as connection:
            tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
            if "catalog_dishes" not in tables:
                return
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(catalog_dishes)")}
            if "category_id" not in columns:
                connection.exec_driver_sql("ALTER TABLE catalog_dishes ADD COLUMN category_id INTEGER")
                connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_catalog_dishes_category_id ON catalog_dishes(category_id)")

    def session(self) -> Iterator[Session]:
        with self.session_factory() as session:
            yield session

    @staticmethod
    def _enable_sqlite_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
