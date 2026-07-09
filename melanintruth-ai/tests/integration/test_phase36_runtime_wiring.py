from app.core.config import Settings
from app.db.repositories.sqlite import SQLiteRepository
from app.services.container import build_runtime_container, repository_from_settings


def test_runtime_wiring_uses_sqlite_for_test_defaults():
    config = Settings(database_url="sqlite:///:memory:")
    repo = repository_from_settings(config)
    assert isinstance(repo, SQLiteRepository)
    container = build_runtime_container(config)
    assert isinstance(container.repo, SQLiteRepository)


def test_runtime_wiring_rejects_missing_production_secret():
    config = Settings(app_env="production", database_url="sqlite:///:memory:", jwt_secret="test-only-change-me")
    try:
        build_runtime_container(config)
        raised = False
    except RuntimeError as exc:
        raised = "JWT_SECRET" in str(exc)
    assert raised
