
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
from app.config import get_settings
from app.di import AppContainer
from app.infra.db.mongo import init_mongo
from app.infra.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
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
        mongo_client.close()
        logger.info("DevMirror stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        RequestLoggingMiddleware,
    )

    register_exception_handlers(app)

    app.include_router(health_router, prefix=settings.health_prefix)
    app.include_router(mock_admin_router, prefix=settings.admin_prefix)
    app.include_router(request_log_router, prefix=settings.request_log_prefix)
    app.include_router(catch_all_router)
    return app


app = create_app()
