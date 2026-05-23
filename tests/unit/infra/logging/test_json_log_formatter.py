import json
import logging
import sys

from app.infra.logging.formatters import JsonLogFormatter


class TestJsonLogFormatter:
    """Проверяет форматирование логов в JSON."""

    def test_json_formatter_produces_valid_json(self) -> None:
        """Проверяет, что форматтер возвращает валидный JSON с базовыми полями."""
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-1"
        record.method = "GET"
        record.path = "/items"
        record.status_code = 200

        payload = json.loads(JsonLogFormatter().format(record))

        assert payload["timestamp"].endswith("Z")
        assert payload["level"] == "INFO"
        assert payload["logger"] == "app.test"
        assert payload["message"] == "hello"
        assert payload["request_id"] == "req-1"
        assert payload["method"] == "GET"
        assert payload["path"] == "/items"
        assert payload["status_code"] == 200

    def test_json_formatter_keeps_extra_fields_unmasked(self) -> None:
        """Проверяет, что дополнительные поля лог-записи сохраняются без маскирования."""
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.request_headers = {"X-Custom-Secret": "raw", "User-Agent": "pytest"}

        payload = json.loads(JsonLogFormatter().format(record))

        assert payload["request_headers"]["X-Custom-Secret"] == "raw"
        assert payload["request_headers"]["User-Agent"] == "pytest"

    def test_exception_logs_contain_type_and_stacktrace(self) -> None:
        """Проверяет, что exception-лог содержит тип ошибки и stacktrace."""
        logger = logging.getLogger("app.test.formatter")
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            record = logger.makeRecord(
                logger.name,
                logging.ERROR,
                __file__,
                1,
                "unexpected_exception",
                (),
                exc_info=sys.exc_info(),
            )

        payload = json.loads(JsonLogFormatter().format(record))

        assert payload["exception_type"] == "RuntimeError"
        assert payload["exception_message"] == "boom"
        assert "RuntimeError: boom" in payload["stacktrace"]
