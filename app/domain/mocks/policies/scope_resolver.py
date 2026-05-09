from collections.abc import Sequence
from typing import Final

from app.domain.request_contexts import RequestContext
from app.domain.shared.ports import ScopeResolutionStrategy


class ChainedScopeResolver:
    """Запускает несколько стратегий, пока одна из них не вернёт непустой scope."""

    def __init__(self, strategies: Sequence[ScopeResolutionStrategy]) -> None:
        self._strategies: Final[list[ScopeResolutionStrategy]] = list(strategies)

    async def resolve_scope(self, request_context: RequestContext) -> str:
        """Возвращает первый доступный scope, найденный стратегиями."""
        for strategy in self._strategies:
            scope = await strategy.resolve(request_context)
            if scope not in (None, ""):
                return scope

        raise RuntimeError(
            "At least one scope resolution strategy must return a scope",
        )
