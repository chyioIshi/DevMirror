"""Celery worker-process state."""

import logging

from app.config import get_app_settings
from app.di.container import AppContainer

logger = logging.getLogger(__name__)


class WorkerState:
    """Owns process-wide Celery worker dependencies."""

    container: AppContainer | None = None

    @classmethod
    def get_container(cls) -> AppContainer:
        if cls.container is None:
            raise RuntimeError("Celery worker container is not initialized")

        return cls.container

    @classmethod
    async def startup(cls) -> None:
        if cls.container is not None:
            return

        logger.info("Initializing Celery worker container")
        cls.container = AppContainer(settings=get_app_settings())
        logger.info("Celery worker container initialized")

    @classmethod
    async def shutdown(cls) -> None:
        if cls.container is None:
            return

        logger.info("Closing Celery worker container")
        await cls.container.aclose()
        cls.container = None
        logger.info("Celery worker container closed")
