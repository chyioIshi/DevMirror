
from functools import lru_cache

from pydantic import MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Хранит конфигурацию приложения из окружения и значений по умолчанию."""

    app_name: str = "DevMirror Mock Service"
    app_version: str = "0.1.0"
    mongo_dsn: MongoDsn = "mongodb://localhost:27017"
    mongo_database: str = "devmirror"
    default_scope: str = "global"
    scope_header_name: str = "x-test-user"
    scope_body_field_name: str = "testUser"
    admin_prefix: str = "/_admin/mocks"
    request_log_prefix: str = "/_admin/request-logs"
    health_prefix: str = "/_health"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
