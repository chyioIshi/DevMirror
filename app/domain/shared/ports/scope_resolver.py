"""Scope resolution ports for incoming requests."""

from typing import Protocol

from app.domain.request_contexts import RequestContext


class ScopeResolutionStrategy(Protocol):
    """Describes one strategy for extracting scope from a request context."""

    async def resolve(self, request_context: RequestContext) -> str | None:
        """Returns a scope candidate or ``None`` when the strategy does not match.

        Args:
            request_context: Incoming request context.

        Returns:
            Scope candidate or ``None``.
        """
        ...


class ScopeResolver(Protocol):
    """Describes a component that resolves the final scope for a request."""

    async def resolve_scope(self, request_context: RequestContext) -> str:
        """Resolves the final scope for an incoming request.

        Args:
            request_context: Incoming request context.

        Returns:
            Resolved scope.
        """
        ...
