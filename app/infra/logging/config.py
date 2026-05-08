import logging.config
from typing import Any

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    logging.config.dictConfig(_build_logging_config(settings))


def _build_logging_config(settings: Settings) -> dict[str, Any]:
    log_level = settings.log_level.upper()

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": "app.infra.logging.filters.RequestContextFilter",
            },
        },
        "formatters": {
            "json": {
                "()": "app.infra.logging.formatters.JsonLogFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["request_context"],
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "app": {"level": log_level, "propagate": True},
            "devmirror": {"level": log_level, "propagate": True},
            "uvicorn": {"level": log_level, "handlers": ["console"], "propagate": False},
            "uvicorn.error": {"level": log_level, "handlers": ["console"], "propagate": False},
            "uvicorn.access": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "pymongo": {"level": "WARNING"},
            "motor": {"level": "WARNING"},
            "beanie": {"level": "WARNING"},
            "httpx": {"level": "WARNING"},
        },
    }
