import pytest

from app.domain.mocks.policies import ChainedScopeResolver
from app.domain.request_contexts import RequestContext


class _StaticStrategy:
    def __init__(self, value: str | None) -> None:
        self._value = value

    async def resolve(self, request_context: RequestContext) -> str | None:  # noqa: ARG002
        return self._value


class TestChainedScopeResolver:
    """Проверяет цепочку стратегий разрешения scope."""

    @pytest.mark.asyncio
    async def test_returns_first_non_empty_scope(self, request_factory) -> None:
        """Проверяет, что resolver возвращает первый непустой scope."""
        resolver = ChainedScopeResolver(
            strategies=[
                _StaticStrategy(None),
                _StaticStrategy("user_id"),
                _StaticStrategy("global"),
            ],
        )

        assert await resolver.resolve_scope(
            request_factory.create_request_context(),
        ) == "user_id"

    @pytest.mark.asyncio
    async def test_skips_empty_string_scope(self, request_factory) -> None:
        """Проверяет, что resolver пропускает пустую строку."""
        resolver = ChainedScopeResolver(
            strategies=[_StaticStrategy(""), _StaticStrategy("global")],
        )

        assert await resolver.resolve_scope(
            request_factory.create_request_context(),
        ) == "global"

    @pytest.mark.asyncio
    async def test_raises_when_no_strategy_returns_scope(self, request_factory) -> None:
        """Проверяет, что resolver падает без подходящего scope."""
        resolver = ChainedScopeResolver(
            strategies=[_StaticStrategy(None), _StaticStrategy("")],
        )

        with pytest.raises(RuntimeError):
            await resolver.resolve_scope(request_factory.create_request_context())
