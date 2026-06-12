"""Application configuration loaded from env vars."""

from functools import lru_cache

from pydantic import Field, MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.infra.side_effects.connection_config import ConnectionConfig


class AppSettings(BaseSettings):
    """Stores runtime settings for the application."""

    app_name: str = "DevMirror Mock Service"
    app_version: str = "0.1.0"
    mongo_dsn: MongoDsn = MongoDsn("mongodb://localhost:27017")
    mongo_database: str = "devmirror"
    default_scope: str = "global"
    scope_header_name: str = "x-test-user"
    scope_body_field_name: str = "testUser"
    admin_prefix: str = "/admin/mocks"
    request_log_prefix: str = "/admin/request-logs"
    health_prefix: str = "/health"
    log_level: str = "INFO"
    side_effect_connections: list[ConnectionConfig] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
    )


@lru_cache
def get_app_settings() -> AppSettings:
    """Return cached application settings.

    Returns:
        Application settings loaded from the env and defaults.
    """
    return AppSettings()
