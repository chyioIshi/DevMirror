import logging.config
from typing import Any

import pytest

from app.config import AppSettings
from app.infra.logging.config import _build_logging_config, configure_logging


class TestLoggingConfig:
    """Проверяет конфигурацию логирования."""

    def test_build_logging_config_uses_uppercase_log_level(self) -> None:
        """Проверяет нормализацию уровня логирования."""
        config = _build_logging_config(AppSettings(log_level="debug"))

        assert config["root"]["level"] == "DEBUG"
        assert config["loggers"]["app"]["level"] == "DEBUG"
        assert config["loggers"]["uvicorn.access"]["level"] == "WARNING"

    def test_build_logging_config_registers_formatter_filter_and_handler(self) -> None:
        """Проверяет основные элементы logging config."""
        config = _build_logging_config(AppSettings())

        assert config["filters"]["request_context"]["()"] == (
            "app.infra.logging.filters.RequestContextFilter"
        )
        assert config["formatters"]["json"]["()"] == (
            "app.infra.logging.formatters.JsonLogFormatter"
        )
        assert config["handlers"]["console"]["formatter"] == "json"
        assert config["handlers"]["console"]["filters"] == ["request_context"]

    def test_configure_logging_passes_config_to_dict_config(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет передачу собранного config в logging.dictConfig."""
        captured_config: dict[str, Any] = {}

        def fake_dict_config(config: dict[str, Any]) -> None:
            captured_config.update(config)

        monkeypatch.setattr(logging.config, "dictConfig", fake_dict_config)

        configure_logging(AppSettings(log_level="error"))

        assert captured_config["root"]["level"] == "ERROR"
