import logging

from app.infra.logging.context import reset_logging_context, set_logging_context
from app.infra.logging.filters import RequestContextFilter


class TestRequestContextFilter:
    """Проверяет фильтр контекста логирования."""

    def test_filter_adds_context_fields_to_record(self) -> None:
        """Проверяет добавление request_id и correlation_id в log record."""
        request_token, correlation_token = set_logging_context(
            request_id="request-1",
            correlation_id="correlation-1",
        )
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="message",
            args=(),
            exc_info=None,
        )

        try:
            result = RequestContextFilter().filter(record)
        finally:
            reset_logging_context(request_token, correlation_token)

        assert result is True
        assert record.request_id == "request-1"
        assert record.correlation_id == "correlation-1"

    def test_filter_uses_none_when_context_is_empty(self) -> None:
        """Проверяет пустые значения при отсутствии контекста."""
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="message",
            args=(),
            exc_info=None,
        )

        result = RequestContextFilter().filter(record)

        assert result is True
        assert record.request_id is None
        assert record.correlation_id is None
