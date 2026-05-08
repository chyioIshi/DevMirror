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
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        headers = _headers(scope)
        request_id = headers.get("x-request-id") or generate_request_id()
        correlation_id = headers.get("x-correlation-id") or request_id
        request_token, correlation_token = set_logging_context(request_id, correlation_id)

        method = str(scope.get("method", ""))
        path = str(scope.get("path", ""))
        started_at = time.perf_counter()
        status_code: int | None = None
        request_body = bytearray()
        response_body = bytearray()
        failed = False

        async def receive_wrapper() -> Message:
            message = await receive()
            if message["type"] == "http.request":
                _extend_limited(request_body, message.get("body", b""))
            return message

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                response_headers = list(message.get("headers", []))
                _set_raw_header(response_headers, b"x-request-id", request_id.encode())
                _set_raw_header(response_headers, b"x-correlation-id", correlation_id.encode())
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
    return logging.ERROR if status_code >= 400 else logging.INFO


def _duration_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 3)


def _headers(scope: Scope) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


def _set_raw_header(headers: list[tuple[bytes, bytes]], name: bytes, value: bytes) -> None:
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
    remaining = BODY_LOG_LIMIT_BYTES - len(target)
    if remaining > 0:
        target.extend(body[:remaining])


def _decode_body(body: bytes) -> Any:
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except ValueError:
        return text
