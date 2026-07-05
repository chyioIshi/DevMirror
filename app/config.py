"""Application configuration loaded from env vars."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, MongoDsn, model_validator
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
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    favicon_path: str = "/favicon.ico"
    log_level: str = "INFO"
    side_effect_connections: list[ConnectionConfig] = Field(default_factory=list)
    async_task_scheduler: Literal["in_process", "celery"] = "in_process"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str | None = None
    celery_task_queue: str = "side_effects.default"
    celery_ignore_result: bool = True
    celery_task_acks_late: bool = True
    celery_task_reject_on_worker_lost: bool = True
    celery_task_time_limit: int | None = Field(default=None, ge=1)
    celery_task_soft_time_limit: int | None = Field(default=None, ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",
    )

    @model_validator(mode="after")
    def validate_celery_time_limits(self) -> Self:
        """Validate Celery worker task time limit ordering."""
        if (
            self.celery_task_time_limit is not None
            and self.celery_task_soft_time_limit is not None
            and self.celery_task_soft_time_limit > self.celery_task_time_limit
        ):
            raise ValueError(
                "celery_task_soft_time_limit must be less than or equal to celery_task_time_limit",
            )
        return self


@lru_cache
def get_app_settings() -> AppSettings:
    """Return cached application settings.

    Returns:
        Application settings loaded from the env and defaults.
    """
    return AppSettings()
