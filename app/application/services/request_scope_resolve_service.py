
from collections.abc import Sequence
from typing import Final

from fastapi import Request

from app.domain.services.scope_resolver import ScopeResolutionStrategy


class RequestScopeResolveService:
    """Запускает несколько стратегий, пока одна из них не вернёт непустой scope."""

    def __init__(
        self,
        strategies: Sequence[ScopeResolutionStrategy],
    ) -> None:
        """Инициализирует резолвер упорядоченным списком стратегий."""
        self._strategies: Final[list[ScopeResolutionStrategy]] = list(strategies)

    async def resolve_scope(self, request: Request) -> str:
        """Возвращает первый доступный scope, найденный стратегиями."""
        for strategy in self._strategies:
            scope = await strategy.resolve(request)
            if scope not in (None, ""):
                return scope

        raise RuntimeError("At least one scope resolution strategy must return a scope")