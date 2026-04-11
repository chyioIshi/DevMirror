
from typing import Protocol

from fastapi import Request


class ScopeResolutionStrategy(Protocol):
    """Описывает одну стратегию извлечения scope из запроса."""

    async def resolve(self, request: Request) -> str | None:
        """Возвращает кандидат на scope или ``None``,
        если стратегия не сработала."""
        ...


class ScopeResolver(Protocol):
    """Описывает компонент, который определяет scope для запроса."""

    async def resolve_scope(self, request: Request) -> str:
        """Определяет итоговый scope для входящего запроса."""
        ...