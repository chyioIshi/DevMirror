import importlib
import sys

import httpx
import pytest
from fastapi import FastAPI

import app.config as config_module
import app.infra.logging as logging_module
from app.api.middleware.logging_middleware import RequestLoggingMiddleware
from app.application.exceptions import MockNotFoundError
from app.config import Settings
from tests.testkit.fakes import FakeMongoClient


def _import_main():
    sys.modules.pop("app.main", None)
    return importlib.import_module("app.main")


class TestMainApp:
    """Проверяет сборку FastAPI приложения."""

    def test_create_app_registers_routes_middleware_and_handlers(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет основную конфигурацию приложения."""
        settings = Settings(
            app_name="Test DevMirror",
            app_version="1.2.3",
            admin_prefix="/admin/mocks",
            request_log_prefix="/admin/request-logs",
            health_prefix="/health",
        )
        configured_settings: list[Settings] = []

        def fake_configure_logging(value: Settings) -> None:
            configured_settings.append(value)

        monkeypatch.setattr(config_module, "get_settings", lambda: settings)
        monkeypatch.setattr(logging_module, "configure_logging", fake_configure_logging)
        main = _import_main()
        configured_settings.clear()

        app = main.create_app()

        route_paths = {route.path for route in app.routes}
        assert app.title == "Test DevMirror"
        assert app.version == "1.2.3"
        assert configured_settings == [settings]
        assert any(middleware.cls is RequestLoggingMiddleware for middleware in app.user_middleware)
        assert "/health" in route_paths
        assert "/admin/mocks" in route_paths
        assert "/admin/request-logs" in route_paths
        assert "/{path:path}" in route_paths
        assert MockNotFoundError in app.exception_handlers

    async def test_lifespan_initializes_container_and_closes_mongo(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет startup и shutdown lifecycle."""
        settings = Settings(mongo_database="test-db")
        mongo_client = FakeMongoClient()

        async def fake_init_mongo(value: Settings) -> FakeMongoClient:
            assert value is settings
            return mongo_client

        monkeypatch.setattr(config_module, "get_settings", lambda: settings)
        monkeypatch.setattr(logging_module, "configure_logging", lambda _: None)
        main = _import_main()
        monkeypatch.setattr(main, "init_mongo", fake_init_mongo)
        app = FastAPI()

        async with main.lifespan(app):
            assert app.state.container.settings is settings
            assert app.state.mongo_client is mongo_client
            assert mongo_client.close_called is False

        assert mongo_client.close_called is True

    async def test_created_app_health_route_works(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет, что созданное приложение обрабатывает health route."""
        monkeypatch.setattr(config_module, "get_settings", lambda: Settings())
        monkeypatch.setattr(logging_module, "configure_logging", lambda _: None)
        main = _import_main()
        app = main.create_app()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200