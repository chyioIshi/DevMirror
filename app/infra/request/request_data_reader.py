import json
from typing import Any, cast

from fastapi import Request


class RequestDataReader:
    """Кэширует разные представления тела входящего запроса."""

    _JSON_NOT_PARSED: object = object()

    async def get_body_bytes(self, request: Request) -> bytes:
        """Возвращает сырые байты тела запроса и кэширует их в состоянии запроса."""
        cached: bytes | None = getattr(request.state, "cached_body_bytes", None)
        if cached is not None:
            return cached

        body = await request.body()
        request.state.cached_body_bytes = body
        return body

    async def get_text(self, request: Request) -> str | None:
        """Возвращает тело запроса как UTF-8 текст."""
        cached: str | None = getattr(request.state, "cached_body_text", None)
        if cached is not None:
            return cached

        body = await self.get_body_bytes(request)
        if not body:
            request.state.cached_body_text = None
            return None

        text = body.decode("utf-8", errors="replace")
        request.state.cached_body_text = text
        return text

    async def get_json(self, request: Request) -> Any | None:
        """Разбирает тело запроса как JSON и кэширует результат."""
        cached: object = getattr(request.state, "cached_body_json", self._JSON_NOT_PARSED)
        if cached is not self._JSON_NOT_PARSED:
            return cast(Any | None, cached)

        text = await self.get_text(request)
        if text is None:
            request.state.cached_body_json = None
            return None

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None

        request.state.cached_body_json = parsed
        return parsed
