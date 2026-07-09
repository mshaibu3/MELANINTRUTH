from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:
    BaseSettings = object  # type: ignore[assignment]
    SettingsConfigDict = dict  # type: ignore[assignment]


if BaseSettings is object:
    @dataclass
    class Settings:
        app_env: str = os.getenv("APP_ENV", "test")
        database_url: str = os.getenv("DATABASE_URL", "sqlite:///:memory:")
        jwt_secret: str = os.getenv("JWT_SECRET", "test-only-change-me")
        jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
        refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
        cors_allowed_origins: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
        object_storage_backend: str = os.getenv("OBJECT_STORAGE_BACKEND", "local")
        local_storage_root: str = os.getenv("LOCAL_STORAGE_ROOT", "/tmp/melanintruth-images")
        max_image_bytes: int = int(os.getenv("MAX_IMAGE_BYTES", "10485760"))
        enable_cloud_processing: bool = os.getenv("ENABLE_CLOUD_PROCESSING", "true").lower() == "true"
        log_level: str = os.getenv("LOG_LEVEL", "INFO")

        def validate_production(self) -> None:
            if self.app_env == "production" and self.jwt_secret in {"", "test-only-change-me", "dev-only-change-with-env"}:
                raise RuntimeError("JWT_SECRET must be set to a non-test value in production")
else:
    class Settings(BaseSettings):
        app_env: str = "test"
        database_url: str = "sqlite:///:memory:"
        jwt_secret: str = "test-only-change-me"
        jwt_algorithm: str = "HS256"
        access_token_minutes: int = 15
        refresh_token_days: int = 30
        cors_allowed_origins: str = "http://localhost:3000,http://localhost:3001"
        object_storage_backend: str = "local"
        local_storage_root: str = "/tmp/melanintruth-images"
        max_image_bytes: int = 10_485_760
        enable_cloud_processing: bool = True
        log_level: str = "INFO"
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        def validate_production(self) -> None:
            if self.app_env == "production" and self.jwt_secret in {"", "test-only-change-me", "dev-only-change-with-env"}:
                raise RuntimeError("JWT_SECRET must be set to a non-test value in production")


settings = Settings()
# Backwards-compatible aliases for older modules.
settings.jwt_secret_key = settings.jwt_secret  # type: ignore[attr-defined]
settings.jwt_access_ttl_minutes = settings.access_token_minutes  # type: ignore[attr-defined]
settings.jwt_refresh_ttl_days = settings.refresh_token_days  # type: ignore[attr-defined]
settings.secure_cookies = settings.app_env == "production"  # type: ignore[attr-defined]
