import pytest

import app.config as app_config
from app.api.routes.catch_all_routes import MockCatchAllRoute
from app.config import AppSettings


class TestMockCatchAllRoute:
    def test_reserved_paths_are_loaded_from_settings(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        settings = AppSettings(
            admin_prefix="/mock-admin",
            request_log_prefix="/mock-logs",
            health_prefix="/status",
            openapi_url="/schema.json",
            docs_url="/api-docs",
            redoc_url="/api-redoc",
            favicon_path="/assets/favicon.ico",
        )
        monkeypatch.setattr(app_config, "get_app_settings", lambda: settings)

        assert MockCatchAllRoute.is_reserved_path("/mock-admin")
        assert MockCatchAllRoute.is_reserved_path("/mock-logs")
        assert MockCatchAllRoute.is_reserved_path("/status")
        assert MockCatchAllRoute.is_reserved_path("/schema.json")
        assert MockCatchAllRoute.is_reserved_path("/api-docs")
        assert MockCatchAllRoute.is_reserved_path("/api-redoc")
        assert MockCatchAllRoute.is_reserved_path("/assets/favicon.ico")

    def test_path_below_reserved_prefix_is_reserved(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        settings = AppSettings(admin_prefix="/mock-admin")
        monkeypatch.setattr(app_config, "get_app_settings", lambda: settings)

        assert MockCatchAllRoute.is_reserved_path("/mock-admin/123")

    def test_regular_mock_path_is_not_reserved(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        settings = AppSettings(admin_prefix="/mock-admin")
        monkeypatch.setattr(app_config, "get_app_settings", lambda: settings)

        assert not MockCatchAllRoute.is_reserved_path("/users/42")
