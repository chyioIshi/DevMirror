from contextvars import ContextVar, Token
from uuid import uuid4

request_ctx: ContextVar[str | None] = ContextVar("request_ctx", default=None)
correlation_ctx: ContextVar[str | None] = ContextVar("correlation_ctx", default=None)


def get_request_id() -> str | None:
    """Получить текущий request_id из контекста."""
    return request_ctx.get()


def get_correlation_id() -> str | None:
    """Получить текущий correlation_id из контекста."""
    return correlation_ctx.get()


def generate_request_id() -> str:
    """Сгенерировать новый request_id."""
    return str(uuid4())


def set_logging_context(
    request_id: str,
    correlation_id: str,
) -> tuple[Token[str | None], Token[str | None]]:
    """Установить request_id и correlation_id в контекст request_ctx и correlation_ctx."""
    request_token = request_ctx.set(request_id)
    correlation_token = correlation_ctx.set(correlation_id)
    return request_token, correlation_token


def reset_logging_context(
    request_token: Token[str | None],
    correlation_token: Token[str | None],
) -> None:
    """Сбросить request_id и correlation_id в контексте request_ctx и correlation_ctx."""
    correlation_ctx.reset(correlation_token)
    request_ctx.reset(request_token)
