
import logging
import logging.config

_LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "app": {"level": "INFO", "propagate": True},
        "uvicorn.access": {"level": "WARNING", "propagate": True},
    },
}


def configure_logging() -> None:
    """Настраивает глобальное логирование приложения."""
    logging.config.dictConfig(_LOGGING_CONFIG)
