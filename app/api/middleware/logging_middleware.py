"""ASGI middleware для логирования HTTP-запросов и корреляционных id."""

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
    """Логирует HTTP-запросы, ответы и добавляет request/correlation id."""

    def __init__(self, app: ASGIApp) -> None:
        """Инициализирует middleware ASGI-приложением.

        Args:
            app: Следующее ASGI-приложение в цепочке middleware.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Обрабатывает ASGI-вызов и логирует завершение HTTP-запроса.

        Args:
            scope: ASGI scope текущего соединения.
            receive: ASGI receive callable.
            send: ASGI send callable.

        Raises:
            Exception: Повторно пробрасывает исключение нижележащего приложения после логирования.
        """
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
            """Сохраняет ограниченную копию тела запроса и передает сообщение дальше.

            Returns:
                Исходное ASGI-сообщение от `receive`.
            """
            message = await receive()
            if message["type"] == "http.request":
                _extend_limited(request_body, message.get("body", b""))
            return message

        async def send_wrapper(message: Message) -> None:
            """Добавляет correlation headers и сохраняет ограниченную копию тела ответа.

            Args:
                message: ASGI-сообщение, отправляемое клиенту.
            """
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
    """Пишет структурированный лог завершенного HTTP-запроса.

    Args:
        level: Уровень логирования.
        **kwargs: Поля события HTTP-запроса и необязательные тела запроса/ответа.
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
    """Определяет уровень логирования по HTTP-статусу.

    Args:
        status_code: HTTP-статус ответа.

    Returns:
        `logging.ERROR` для 4xx/5xx и `logging.INFO` для остальных статусов.
    """
    return logging.ERROR if status_code >= 400 else logging.INFO


def _duration_ms(started_at: float) -> float:
    """Вычисляет длительность запроса в миллисекундах.

    Args:
        started_at: Значение `time.perf_counter()` на старте запроса.

    Returns:
        Длительность выполнения в миллисекундах.
    """
    return round((time.perf_counter() - started_at) * 1000, 3)


def _headers(scope: Scope) -> dict[str, str]:
    """Извлекает HTTP-заголовки из ASGI scope.

    Args:
        scope: ASGI scope текущего HTTP-запроса.

    Returns:
        Словарь заголовков с ключами в нижнем регистре.
    """
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


def _set_raw_header(headers: list[tuple[bytes, bytes]], name: bytes, value: bytes) -> None:
    """Устанавливает raw HTTP-заголовок в списке ASGI headers.

    Args:
        headers: Изменяемый список raw headers.
        name: Имя заголовка в bytes.
        value: Значение заголовка в bytes.
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
    """Добавляет фрагмент тела, не превышая лимит логирования.

    Args:
        target: Буфер, в который добавляется тело.
        body: Очередной фрагмент тела запроса или ответа.
    """
    remaining = BODY_LOG_LIMIT_BYTES - len(target)
    if remaining > 0:
        target.extend(body[:remaining])


def _decode_body(body: bytes) -> Any:
    """Декодирует тело запроса или ответа для структурированного лога.

    Args:
        body: Тело запроса или ответа в bytes.

    Returns:
        JSON-значение, если тело содержит JSON, иначе строку.
    """
    text = body.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except ValueError:
        return text
