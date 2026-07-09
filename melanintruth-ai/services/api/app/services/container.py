from __future__ import annotations

import logging
from typing import Any

from app.backend.repository import InMemoryRepository
from app.core.config import Settings, settings
from app.db.repositories.sqlite import SQLiteRepository
from app.db.session import connect_sqlite
from app.services.wiring import ServiceContainer, build_container

logger = logging.getLogger(__name__)


def _redacted_database_label(database_url: str) -> str:
    scheme = database_url.split(":", 1)[0] if database_url else "missing"
    host_part = database_url.rsplit("@", 1)[-1] if "@" in database_url else database_url
    host = host_part.split("/", 1)[0].replace("postgresql+psycopg://", "")
    return f"{scheme}://{host or 'configured'}"


def repository_from_settings(config: Settings = settings, sql_session: Any | None = None) -> Any:
    """Select a runtime repository from configuration without unsafe fallback.

    * `memory://` is allowed only outside production for dependency-light tests.
    * SQLite URLs use the dependency-light SQLiteRepository outside production.
    * PostgreSQL/other SQL URLs use SQLModelRepository when SQLModel and a DB session are
      available; production fails fast instead of silently using memory or SQLite.
    """
    database_url = (config.database_url or "").strip()
    if config.app_env == "production" and (not database_url or database_url.startswith(("sqlite", "memory"))):
        raise RuntimeError("Production requires a non-SQLite DATABASE_URL and SQL repository mode")
    if database_url.startswith("memory"):
        if config.app_env == "production":
            raise RuntimeError("Production cannot use in-memory repository mode")
        logger.info("Repository mode selected: memory")
        return InMemoryRepository()
    if database_url.startswith("sqlite"):
        sqlite_path = ":memory:" if database_url.endswith(":memory:") else database_url.replace("sqlite:///", "", 1)
        logger.info("Repository mode selected: sqlite")
        return SQLiteRepository(connect_sqlite(sqlite_path))
    try:
        from app.db.repositories.sqlmodel_runtime import SQLModelRepository, SQLSession
    except ModuleNotFoundError as exc:
        if config.app_env == "production":
            raise RuntimeError("SQLModel dependencies are required for production database URLs") from exc
        logger.info("Repository mode selected: sqlite-fallback; sql dependencies unavailable")
        return SQLiteRepository(connect_sqlite())
    if SQLSession is None or sql_session is None:
        if config.app_env == "production":
            raise RuntimeError("A SQLModel Session is required for production database URLs")
        logger.info("Repository mode selected: sqlite-fallback; sql session unavailable")
        return SQLiteRepository(connect_sqlite())
    logger.info("Repository mode selected: sqlmodel database=%s", _redacted_database_label(database_url))
    return SQLModelRepository(sql_session)


def build_runtime_container(config: Settings = settings, sql_session: Any | None = None) -> ServiceContainer:
    config.validate_production()
    return build_container(repository_from_settings(config, sql_session))
