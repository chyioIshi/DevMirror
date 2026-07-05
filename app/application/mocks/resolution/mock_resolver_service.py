"""Application service for resolving incoming requests to mocks."""

from collections.abc import Sequence
from typing import Final

from app.application.exceptions import MockNotFoundError
from app.application.mocks.resolution.strategies import MockResolveStrategy
from app.domain.mocks.models.resolution import ResolvedMock
from app.domain.request_contexts import RequestContext


class MockResolverService:
    """Orchestrates mock resolution strategies in priority order."""

    def __init__(self, strategies: Sequence[MockResolveStrategy]) -> None:
        """Initializes the mock resolver service.

        Args:
            strategies: Resolver strategies ordered by priority.
        """
        self._strategies: Final[tuple[MockResolveStrategy, ...]] = tuple(strategies)

    async def resolve(self, request_context: RequestContext) -> ResolvedMock:
        """Returns the first mock resolved by the configured strategies.

        Args:
            request_context: Incoming request context with method, path, and request data.

        Returns:
            Resolved mock selected by the first matching strategy.

        Raises:
            MockNotFoundError: If no strategy resolves the request.
        """
        for strategy in self._strategies:
            resolved_mock = await strategy.resolve(request_context)
            if resolved_mock is not None:
                return resolved_mock

        raise MockNotFoundError(
            "No active mock matched the request",
            details={
                "method": str(request_context.method),
                "path": request_context.path,
            },
        )
