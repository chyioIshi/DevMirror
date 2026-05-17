from typing import Any

import pytest
from fastapi import Request

from app.domain.shared import HttpMethod
from app.infra.context.request_context_resolver import RequestContextResolver


class _FakeRequestDataAccessor:
    def __init__(self, *, json_body: Any | None, text_body: str | None = None) -> None:
        self.json_body = json_body
        self.text_body = text_body

    async def get_body_bytes(self, request: Request) -> bytes:  # noqa: ARG002
        return b""

    async def get_text(self, request: Request) -> str | None:  # noqa: ARG002
        return self.text_body

    async def get_json(self, request: Request) -> Any | None:  # noqa: ARG002
        return self.json_body


class TestRequestContextResolver:
    """Проверяет создание domain model RequestContext из API request."""

    @pytest.mark.asyncio
    async def test_resolve_uses_json_body_when_available(self, request_factory) -> None:
        """Проверяет, что json body имеет приоритет над text body."""
        request = request_factory.create_starlette_request(
            method="POST",
            path="/users",
            headers={"user": "user1"},
            query_string="tag=a&tag=b&page=1",
        )
        resolver = RequestContextResolver(
            _FakeRequestDataAccessor(
                json_body={"ok": True},
                text_body="text",
            ),
        )

        context = await resolver.resolve(request)

        assert context.method == HttpMethod.POST
        assert context.path == "/users"
        assert context.headers["user"] == "user1"
        assert context.query_params == {"tag": ["a", "b"], "page": "1"}
        assert context.body == {"ok": True}

    @pytest.mark.asyncio
    async def test_resolve_falls_back_to_text_body(self, request_factory) -> None:
        """Проверяет fallback на text body, если json body = None."""
        request = request_factory.create_starlette_request(path="/plain")
        resolver = RequestContextResolver(
            _FakeRequestDataAccessor(json_body=None, text_body="plain-text"),
        )

        context = await resolver.resolve(request)

        assert context.body == "plain-text"
