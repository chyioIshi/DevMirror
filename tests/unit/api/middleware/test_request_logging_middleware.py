import logging
from typing import Any

import pytest
from starlette.types import Message, Receive, Scope, Send

from app.api.middleware.logging_middleware import (
    BODY_LOG_LIMIT_BYTES,
    RequestLoggingMiddleware,
    _extend_limited,
    _set_raw_header,
)


# helpers
def _http_scope(
    *,
    headers: list[tuple[bytes, bytes]] | None = None,
    state: dict[str, Any] | None = None,
) -> Scope:
    return {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "headers": headers or [],
        "state": state or {},
    }


def _message_receive(message: Message) -> Receive:
    async def receive() -> Message:
        return message

    return receive


async def _empty_receive() -> Message:
    return {"type": "http.disconnect"}


async def _empty_send(message: Message) -> None:
    return None


def _collect_send(messages: list[Message]) -> Send:
    async def send(message: Message) -> None:
        messages.append(message)

    return send


def _last_http_log_record(records: list[logging.LogRecord]) -> logging.LogRecord:
    return [record for record in records if record.name == "app.http"][-1]


class TestRequestLoggingMiddleware:
    """Проверяет RequestLoggingMiddleware."""

    async def test_non_http_scope_is_passed_to_app(self) -> None:
        """Проверяет, что non-http scope передается без обработки."""
        called_scopes: list[Scope] = []

        async def app(scope: Scope, receive: Receive, send: Send) -> None:
            called_scopes.append(scope)

        middleware = RequestLoggingMiddleware(app)
        scope: Scope = {"type": "lifespan"}

        await middleware(scope, _empty_receive, _empty_send)

        assert called_scopes == [scope]

    async def test_successful_request_adds_headers_and_logs_bodies(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Проверяет логирование успешного HTTP-запроса."""

        async def app(scope: Scope, receive: Receive, send: Send) -> None:
            await receive()
            await send(
                {
                    "type": "http.response.start",
                    "status": 201,
                    "headers": [
                        (b"x-request-id", b"old-request"),
                        (b"x-request-id", b"duplicate-request"),
                    ],
                },
            )
            await send({"type": "http.response.body", "body": b'{"ok": true}'})

        sent_messages: list[Message] = []
        middleware = RequestLoggingMiddleware(app)
        caplog.set_level(logging.INFO, logger="app.http")

        await middleware(
            _http_scope(headers=[(b"x-request-id", b"request-1")]),
            _message_receive({"type": "http.request", "body": b'{"input": true}'}),
            _collect_send(sent_messages),
        )

        response_start = sent_messages[0]
        response_headers = dict(response_start["headers"])
        log_record = _last_http_log_record(caplog.records)
        assert response_headers[b"x-request-id"] == b"request-1"
        assert response_headers[b"x-correlation-id"] == b"request-1"
        assert log_record.status_code == 201
        assert log_record.request_body == {"input": True}
        assert log_record.response_body == {"ok": True}

    async def test_failed_request_is_logged_and_reraised(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Проверяет логирование исключения из downstream app."""

        async def app(scope: Scope, receive: Receive, send: Send) -> None:
            await receive()
            raise RuntimeError("boom")

        middleware = RequestLoggingMiddleware(app)
        caplog.set_level(logging.ERROR, logger="app.http")
        scope = _http_scope(state={"exception_logged": True})

        with pytest.raises(RuntimeError, match="boom"):
            await middleware(
                scope,
                _message_receive({"type": "http.request", "body": b"plain body"}),
                _empty_send,
            )

        log_record = _last_http_log_record(caplog.records)
        assert log_record.status_code == 500
        assert log_record.request_body == "plain body"
        assert log_record.exc_info is False

    def test_set_raw_header_replaces_first_header_and_removes_duplicates(self) -> None:
        """Проверяет замену первого header и удаление дублей."""
        headers = [
            (b"x-test", b"old"),
            (b"x-other", b"value"),
            (b"x-test", b"duplicate"),
        ]

        _set_raw_header(headers, b"x-test", b"new")

        assert headers == [(b"x-test", b"new"), (b"x-other", b"value")]

    def test_extend_limited_does_not_extend_full_buffer(self) -> None:
        """Проверяет ограничение размера логируемого body."""
        body = bytearray(b"x" * BODY_LOG_LIMIT_BYTES)

        _extend_limited(body, b"overflow")

        assert body == bytearray(b"x" * BODY_LOG_LIMIT_BYTES)
