import logging

import pytest

from app.config import AppSettings
from app.infra.celery import signals
from app.infra.logging.filters import RequestContextFilter


class TestCelerySignals:
    def test_process_init_creates_container(self, monkeypatch) -> None:
        calls: list[bool] = []

        async def startup() -> None:
            calls.append(True)

        monkeypatch.setattr(
            "app.infra.celery.signals.WorkerState.startup",
            startup,
        )

        signals.create_celery_container_on_worker_process_init()

        assert calls == [True]

    def test_process_init_logs_and_reraises_container_errors(
        self,
        monkeypatch,
        caplog,
    ) -> None:
        async def startup() -> None:
            raise RuntimeError("init failed")

        monkeypatch.setattr(
            "app.infra.celery.signals.WorkerState.startup",
            startup,
        )

        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(RuntimeError, match="init failed"),
        ):
            signals.create_celery_container_on_worker_process_init()

        assert any(
            record.message == "celery_worker_container_init_failed" for record in caplog.records
        )

    def test_shutdown_handler_closes_container(self, monkeypatch) -> None:
        calls: list[bool] = []

        async def shutdown() -> None:
            calls.append(True)

        monkeypatch.setattr(
            "app.infra.celery.signals.WorkerState.shutdown",
            shutdown,
        )

        signals.close_celery_container_on_worker_process_shutdown()

        assert calls == [True]

    def test_shutdown_handler_logs_and_suppresses_close_errors(
        self,
        monkeypatch,
        caplog,
    ) -> None:
        async def shutdown() -> None:
            raise RuntimeError("close failed")

        monkeypatch.setattr(
            "app.infra.celery.signals.WorkerState.shutdown",
            shutdown,
        )

        with caplog.at_level(logging.ERROR):
            signals.close_celery_container_on_worker_process_shutdown()

        assert any(
            record.message == "celery_worker_container_shutdown_failed" for record in caplog.records
        )

    def test_setup_logging_uses_application_logging_config(self, monkeypatch) -> None:
        settings = AppSettings(log_level="debug")
        configured_settings: list[AppSettings] = []

        monkeypatch.setattr(
            "app.infra.celery.signals.get_app_settings",
            lambda: settings,
        )
        monkeypatch.setattr(
            "app.infra.celery.signals.configure_logging",
            configured_settings.append,
        )

        signals.setup_celery_logging()

        assert configured_settings == [settings]

    def test_after_setup_logger_adds_request_context_filter(self) -> None:
        logger = logging.Logger("celery-test")

        signals.enrich_celery_logger(logger=logger)

        assert any(isinstance(item, RequestContextFilter) for item in logger.filters)

    def test_after_setup_logger_does_not_duplicate_request_context_filter(self) -> None:
        logger = logging.Logger("celery-test")
        logger.addFilter(RequestContextFilter())

        signals.enrich_celery_logger(logger=logger)

        assert sum(isinstance(item, RequestContextFilter) for item in logger.filters) == 1

    def test_after_setup_logger_allows_missing_logger(self) -> None:
        signals.enrich_celery_logger(logger=None)
