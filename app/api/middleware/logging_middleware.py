"""ASGI middleware for logging HTTP requests and correlation ids."""

import json
import logging
import time
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.infra.logging.context import (
    generate_request_id,
    reset_logging_context,
    set_logging_context,
)

logger = logging.getLogger("app.http")

BODY_LOG_LIMIT_BYTES = 4096


class RequestLoggingMiddleware:
    """Logs HTTP requests and responses and adds request/correlation ids."""

    def __init__(self, app: ASGIApp) -> None:
        """Initializes the middleware with an ASGI application.

        Args:
            app: Next ASGI application in the middleware chain.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handles an ASGI call and logs HTTP request completion.

        Args:
            scope: ASGI scope for the current connection.
            receive: ASGI receive callable.
            send: ASGI send callable.

        Raises:
            Exception: Re-raises exceptions from the downstream application after
                logging.
        """
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        headers = _headers(scope)
        request_id = headers.get("x-request-id") or generate_request_id()
        correlation_id = headers.get("x-correlation-id") or request_id
        request_token, correlation_token = set_logging_context(request_id, correlation_id)  # noqa: E501

        method = str(scope.get("method", ""))
        path = str(scope.get("path", ""))
        started_at = time.perf_counter()
        status_code: int | None = None
        request_body = bytearray()
        response_body = bytearray()
        failed = False

        async def receive_wrapper() -> Message:
            """Stores a limited copy of the request body and forwards the message.

            Returns:
                Original ASGI message from `receive`.
            """
            message = await receive()
            if message["type"] == "http.request":
                _extend_limited(request_body, message.get("body", b""))
            return message

        async def send_wrapper(message: Message) -> None:
            """Adds correlation headers and stores a limited copy of the response body.

            Args:
                message: ASGI message sent to the client.
            """
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                response_headers = list(message.get("headers", []))
                _set_raw_header(response_headers, b"x-request-id", request_id.encode())
                _set_raw_header(response_headers, b"x-correlation-id", correlation_id.encode())  # noqa: E501
                message["headers"] = response_headers
            elif message["type"] == "http.response.body":
                _extend_limited(response_body, message.get("body", b""))

            await send(message)

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except Exception:
            failed = True
            _log_request(
                logging.ERROR,
                request_id=request_id,
                correlation_id=correlation_id,
                method=method,
                path=path,
                status_code=status_code or 500,
                duration_ms=_duration_ms(started_at),
                exc_info=not bool(state.get("exception_logged")),
                request_body=bytes(request_body) if request_body else None,
                response_body=bytes(response_body) if response_body else None,
            )
            raise
        finally:
            if status_code is not None and not failed:
                _log_request(
                    _level_for(status_code),
                    request_id=request_id,
                    correlation_id=correlation_id,
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=_duration_ms(started_at),
                    exc_info=False,
                    request_body=bytes(request_body) if request_body else None,
                    response_body=bytes(response_body) if response_body else None,
                )
            reset_logging_context(request_token, correlation_token)


def _log_request(level: int, **kwargs: Any) -> None:
    """Writes a structured log for a completed HTTP request.

    Args:
        level: Logging level.
        **kwargs: HTTP request event fields and optional request/response bodies.
    """
    request_body = kwargs.pop("request_body", None)
    response_body = kwargs.pop("response_body", None)
    exc_info = bool(kwargs.pop("exc_info", False))
    extra = {"event": "http_request_completed"}
    extra.update({key: value for key, value in kwargs.items() if value is not None})
    if request_body is not None:
        extra["request_body"] = _decode_body(request_body)
    if response_body is not None:
        extra["response_body"] = _decode_body(response_body)
    logger.log(level, "http_request_completed", extra=extra, exc_info=exc_info)


def _level_for(status_code: int) -> int:
    """Determines the logging level from an HTTP status.

    Args:
        status_code: HTTP response status.

    Returns:
        `logging.ERROR` for 4xx/5xx and `logging.INFO` for other statuses.
    """
    return logging.ERROR if status_code >= 400 else logging.INFO


def _duration_ms(started_at: float) -> float:
    """Calculates request duration in milliseconds.

    Args:
        started_at: `time.perf_counter()` value captured at request start.

    Returns:
        Execution duration in milliseconds.
    """
    return round((time.perf_counter() - started_at) * 1000, 3)


def _headers(scope: Scope) -> dict[str, str]:
    """Extracts HTTP headers from an ASGI scope.

    Args:
        scope: ASGI scope for the current HTTP request.

    Returns:
        Header dictionary with lower-case keys.
    """
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


def _set_raw_header(headers: list[tuple[bytes, bytes]], name: bytes, value: bytes) -> None:  # noqa: E501
    """Sets a raw HTTP header in an ASGI headers list.

    Args:
        headers: Mutable raw headers list.
        name: Header name as bytes.
        value: Header value as bytes.
    """
    normalized_name = name.lower()
    matched = False
    index = 0
    while index < len(headers):
        key, _ = headers[index]
        if key.lower() != normalized_name:
            index += 1
            continue
        if matched:
            del headers[index]
            continue
        headers[index] = key, value
        matched = True
        index += 1
    if not matched:
        headers.append((name, value))


def _extend_limited(target: bytearray, body: bytes) -> None:
    """Appends a body fragment without exceeding the logging limit.

    Args:
        target: Buffer receiving the body fragment.
        body: Next request or response body fragment.
    """
    remaining = BODY_LOG_LIMIT_BYTES - len(target)
    if remaining > 0:
        target.extend(body[:remaining])


def _decode_body(body: bytes) -> Any:
    """Decodes a request or response body for structured logging.

    Args:
        body: Request or response body bytes.

    Returns:
        JSON value when the body contains JSON, otherwise a string.
    """
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except ValueError:
        return text
