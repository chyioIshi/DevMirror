from app.api.routes.catch_all_routes import catch_all_router
from app.api.routes.health_routes import health_router
from app.api.routes.mock_admin_routes import mock_admin_router
from app.api.routes.request_log_routes import request_log_router

__all__ = [
    "catch_all_router",
    "health_router",
    "mock_admin_router",
    "request_log_router",
]
