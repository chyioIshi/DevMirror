from typing import Protocol

from app.domain.request_contexts.models.request_context import RequestContext


class ScopeResolutionStrategy(Protocol):
    """Описывает одну стратегию извлечения scope из контекста запроса."""

    async def resolve(self, request_context: RequestContext) -> str | None:
        """Возвращает кандидат на scope или ``None``,
        если стратегия не сработала."""
        ...


class ScopeResolver(Protocol):
    """Описывает компонент, который определяет scope для запроса."""

    async def resolve_scope(self, request_context: RequestContext) -> str:
        """Определяет итоговый scope для входящего запроса."""
        ...
