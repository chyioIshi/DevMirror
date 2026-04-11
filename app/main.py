
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.catch_all_routes import catch_all_router
from app.api.routes.health_routes import health_router
from app.api.routes.mock_admin_routes import mock_admin_router
from app.api.routes.request_log_routes import request_log_router
from app.config import get_settings
from app.di import AppContainer
from app.infra.db.mongo.bootstrap import init_mongo
from app.infra.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings = get_settings()
    container = AppContainer(settings=settings)
    app.state.container = container
    mongo_client = await init_mongo(settings)
    app.state.mongo_client = mongo_client
    logger.info("DevMirror started (mongo_dsn=%s, db=%s)", settings.mongo_dsn, settings.mongo_database)
    try:
        yield
    finally:
        mongo_client.close()
        logger.info("DevMirror stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(health_router, prefix=settings.health_prefix)
    app.include_router(mock_admin_router, prefix=settings.admin_prefix)
    app.include_router(request_log_router, prefix=settings.request_log_prefix)
    app.include_router(catch_all_router)
    return app


app = create_app()
