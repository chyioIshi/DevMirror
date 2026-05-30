"""Request logging context storage."""

from contextvars import ContextVar, Token
from uuid import uuid4

request_ctx: ContextVar[str | None] = ContextVar("request_ctx", default=None)
correlation_ctx: ContextVar[str | None] = ContextVar("correlation_ctx", default=None)


def get_request_id() -> str | None:
    """Returns the current request id.

    Returns:
        Current request id or ``None``.
    """
    return request_ctx.get()


def get_correlation_id() -> str | None:
    """Returns the current correlation id.

    Returns:
        Current correlation id or ``None``.
    """
    return correlation_ctx.get()


def generate_request_id() -> str:
    """Generates a new request id.

    Returns:
        Hex-encoded request id.
    """
    return str(uuid4())


def set_logging_context(
    request_id: str,
    correlation_id: str,
) -> tuple[Token[str | None], Token[str | None]]:
    """Stores request id and correlation id in context variables.

    Args:
        request_id: Request identifier.
        correlation_id: Correlation identifier.

    Returns:
        Tokens that can be used to restore previous context values.
    """
    request_token = request_ctx.set(request_id)
    correlation_token = correlation_ctx.set(correlation_id)
    return request_token, correlation_token


def reset_logging_context(
    request_token: Token[str | None],
    correlation_token: Token[str | None],
) -> None:
    """Restores request id and correlation id context variables.

    Args:
        request_token: Token returned when setting request id.
        correlation_token: Token returned when setting correlation id.
    """
    correlation_ctx.reset(correlation_token)
    request_ctx.reset(request_token)
