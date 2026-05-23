from uuid import UUID

from app.infra.logging.context import (
    generate_request_id,
    get_correlation_id,
    get_request_id,
    reset_logging_context,
    set_logging_context,
)


class TestLoggingContext:
    """Проверяет контекст логирования."""

    def test_set_and_reset_logging_context(self) -> None:
        """Проверяет установку и сброс request_id и correlation_id."""
        request_token, correlation_token = set_logging_context(
            request_id="request-1",
            correlation_id="correlation-1",
        )

        assert get_request_id() == "request-1"
        assert get_correlation_id() == "correlation-1"

        reset_logging_context(request_token, correlation_token)

        assert get_request_id() is None
        assert get_correlation_id() is None

    def test_generate_request_id_returns_uuid(self) -> None:
        """Проверяет генерацию request_id в формате UUID."""
        request_id = generate_request_id()

        assert str(UUID(request_id)) == request_id
