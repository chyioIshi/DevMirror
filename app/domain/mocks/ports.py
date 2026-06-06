"""Ports used by the mocks domain."""

from typing import Protocol

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
)
from app.domain.request_contexts import RequestContext


class ScopeResolutionStrategy(Protocol):
    """Describes one strategy for extracting mock scope from a request context."""

    async def resolve(self, request_context: RequestContext) -> str | None:
        """Returns a scope candidate or ``None`` when the strategy does not match."""
        ...


class ScopeResolver(Protocol):
    """Describes a component that resolves the final mock scope for a request."""

    async def resolve_scope(self, request_context: RequestContext) -> str:
        """Resolves the final mock scope for an incoming request."""
        ...


class SideEffectProvider(Protocol):
    """Domain port implemented by concrete side effect providers."""

    provider: str

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        """Executes a side effect."""
        ...
