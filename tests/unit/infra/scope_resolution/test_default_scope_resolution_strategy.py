import pytest

from app.infra.scope_resolution import DefaultScopeResolutionStrategy


class TestDefaultScopeResolutionStrategy:
    """Проверяет стратегию scope по умолчанию."""

    @pytest.mark.asyncio
    async def test_always_returns_configured_scope(self, request_factory) -> None:
        """Проверяет, что стратегия всегда возвращает настроенный scope."""
        strategy = DefaultScopeResolutionStrategy("global")
        ctx = request_factory.create_request_context()

        assert await strategy.resolve(ctx) == "global"
