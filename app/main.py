"""FastAPI app factory and runtime lifecycle wiring."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.error_handlers import register_exception_handlers
from app.api.middleware.logging_middleware import RequestLoggingMiddleware
from app.api.routes import (
    catch_all_router,
    health_router,
    mock_admin_router,
    request_log_router,
)
from app.config import get_app_settings
from app.di import AppContainer
from app.infra.db.mongo import close_mongo, init_mongo
from app.infra.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage app startup and shutdown resources.

    Args:
        app: FastAPI app instance.

    Yields:
        Control back to FastAPI while the app is running.
    """
    settings = get_app_settings()
    container = AppContainer(settings=settings)
    app.state.container = container
    mongo_client = await init_mongo(settings)
    app.state.mongo_client = mongo_client
    logger.info(
        "DevMirror started",
        extra={
            "mongo_dsn": str(settings.mongo_dsn),
            "db": settings.mongo_database,
        },
    )
    try:
        yield
    finally:
        await container.aclose()
        await close_mongo(mongo_client)
        logger.info("DevMirror stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI app.

    Returns:
        Configured FastAPI app instance.
    """
    app_settings = get_app_settings()
    configure_logging(app_settings)

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        RequestLoggingMiddleware,
    )

    register_exception_handlers(app)

    app.include_router(health_router, prefix=app_settings.health_prefix)
    app.include_router(mock_admin_router, prefix=app_settings.admin_prefix)
    app.include_router(request_log_router, prefix=app_settings.request_log_prefix)
    app.include_router(catch_all_router)
    return app


app = create_app()
