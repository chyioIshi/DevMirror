"""Celery worker lifecycle signal handlers."""

import asyncio
import logging
from typing import Any

from celery.signals import (  # type: ignore[import-untyped]
    after_setup_logger,
    setup_logging,
    worker_process_init,
    worker_process_shutdown,
)

from app.config import get_app_settings
from app.infra.celery.state import WorkerState
from app.infra.logging import configure_logging
from app.infra.logging.filters import RequestContextFilter

logger = logging.getLogger(__name__)


@worker_process_init.connect
def create_celery_container_on_worker_process_init(**_: Any) -> None:
    """Create the worker-process AppContainer during worker process startup."""
    try:
        asyncio.run(WorkerState.startup())
    except Exception:
        logger.exception("celery_worker_container_init_failed")
        raise


@worker_process_shutdown.connect
def close_celery_container_on_worker_process_shutdown(**_: Any) -> None:
    """Close Celery worker resources during worker process shutdown."""
    try:
        asyncio.run(WorkerState.shutdown())
    except Exception:
        logger.exception("celery_worker_container_shutdown_failed")


@setup_logging.connect
def setup_celery_logging(**_: Any) -> None:
    """Configure Celery worker logging through the application logging config."""
    configure_logging(get_app_settings())


@after_setup_logger.connect
def enrich_celery_logger(logger: logging.Logger | None = None, **_: Any) -> None:
    """Ensure Celery loggers include the request context filter."""
    if logger is None:
        return

    if any(isinstance(item, RequestContextFilter) for item in logger.filters):
        return

    logger.addFilter(RequestContextFilter())
