from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "api_fastapi"))

import pytest
from _pytest.outcomes import Failed

from app.backend.repository import InMemoryRepository
from app.db.repositories.sqlite import SQLiteRepository
from app.services.container import repository_from_settings
from api_helpers import require_dependency


@dataclass
class MinimalSettings:
    app_env: str = "test"
    database_url: str = "sqlite:///:memory:"
    jwt_secret: str = "test-only-change-me"

    def validate_production(self) -> None:
        return None


def test_require_fastapi_tests_flag_turns_missing_dependency_skip_into_failure(monkeypatch):
    monkeypatch.setenv("REQUIRE_FASTAPI_TESTS", "1")
    with pytest.raises(Failed):
        require_dependency("definitely_missing_phase38_dependency")


def test_test_mode_can_choose_in_memory_repository():
    repo = repository_from_settings(MinimalSettings(database_url="memory://phase38"))
    assert isinstance(repo, InMemoryRepository)


def test_test_mode_can_choose_sqlite_repository():
    repo = repository_from_settings(MinimalSettings(database_url="sqlite:///:memory:"))
    assert isinstance(repo, SQLiteRepository)


def test_production_without_sql_database_url_fails_fast():
    with pytest.raises(RuntimeError):
        repository_from_settings(MinimalSettings(app_env="production", database_url=""))
    with pytest.raises(RuntimeError):
        repository_from_settings(MinimalSettings(app_env="production", database_url="sqlite:///:memory:"))


def test_repository_mode_logging_redacts_database_credentials(caplog):
    settings = MinimalSettings(database_url="postgresql+psycopg://user:secret-password@example.test:5432/db")
    caplog.set_level(logging.INFO, logger="app.services.container")
    repository_from_settings(settings)
    text = caplog.text
    assert "secret-password" not in text
    assert "Repository mode selected" in text
