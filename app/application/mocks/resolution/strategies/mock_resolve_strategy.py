"""Resolver strategy contract."""

from typing import Protocol

from app.domain.mocks.models.resolution import ResolvedMock
from app.domain.request_contexts import RequestContext


class MockResolveStrategy(Protocol):
    """Strategy contract for resolving one incoming request to a mock."""

    async def resolve(self, request_context: RequestContext) -> ResolvedMock | None:
        """Returns a resolved mock or ``None`` when the strategy cannot resolve it."""
        ...
