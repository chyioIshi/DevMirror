"""Policy for resolving request scope with multiple strategies."""

from collections.abc import Sequence
from typing import Final

from app.domain.mocks.ports import ScopeResolutionStrategy
from app.domain.request_contexts import RequestContext


class ChainedScopeResolver:
    """Runs strategies until one of them returns a non-empty scope."""

    def __init__(self, strategies: Sequence[ScopeResolutionStrategy]) -> None:
        """Initializes the resolver with scope resolution strategies.

        Args:
            strategies: Scope resolution strategies in execution order.
        """
        self._strategies: Final[list[ScopeResolutionStrategy]] = list(strategies)

    async def resolve_scope(self, request_context: RequestContext) -> str:
        """Returns the first available scope found by configured strategies.

        Args:
            request_context: Incoming request context.

        Returns:
            Resolved request scope.

        Raises:
            RuntimeError: If no configured strategy returns a scope.
        """
        for strategy in self._strategies:
            scope = await strategy.resolve(request_context)
            if scope is not None and scope != "":
                return scope

        raise RuntimeError(
            "At least one scope resolution strategy must return a scope",
        )
