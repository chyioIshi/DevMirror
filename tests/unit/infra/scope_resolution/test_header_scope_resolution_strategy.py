import pytest

from app.infra.scope_resolution import HeaderScopeResolutionStrategy


class TestHeaderScopeResolutionStrategy:
    """Проверяет стратегию разрешения scope из HTTP-заголовка."""

    @pytest.mark.asyncio
    async def test_returns_header_value_when_present(self, request_factory) -> None:
        """Проверяет, что стратегия возвращает значение существующего заголовка."""
        strategy = HeaderScopeResolutionStrategy("X-Scope")
        ctx = request_factory.create_request_context(headers={"X-Scope": "user_id"})

        assert await strategy.resolve(ctx) == "user_id"

    @pytest.mark.asyncio
    async def test_returns_none_when_header_missing(self, request_factory) -> None:
        """Проверяет, что стратегия возвращает None при отсутствии заголовка."""
        strategy = HeaderScopeResolutionStrategy("X-Scope")
        ctx = request_factory.create_request_context(headers={"Other": "x"})

        assert await strategy.resolve(ctx) is None

    @pytest.mark.asyncio
    async def test_returns_none_when_header_empty(self, request_factory) -> None:
        """Проверяет, что стратегия возвращает None для пустого заголовка."""
        strategy = HeaderScopeResolutionStrategy("X-Scope")
        ctx = request_factory.create_request_context(headers={"X-Scope": ""})

        assert await strategy.resolve(ctx) is None
