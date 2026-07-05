from app.application.exceptions import MockNotFoundError
from app.domain.mocks.models.resolution import ResolvedMock
from app.domain.request_contexts import RequestContext


class FakeMockResolverService:
    """Fake MockResolverService для integration-тестов catch-all route."""

    def __init__(self, resolved_mock: ResolvedMock | None) -> None:
        self.resolved_mock = resolved_mock
        self.resolve_calls: list[RequestContext] = []

    async def resolve(self, request_context: RequestContext) -> ResolvedMock:
        """Возвращает заранее заданный результат резолва."""
        self.resolve_calls.append(request_context)
        if self.resolved_mock is None:
            raise MockNotFoundError(
                "No active mock matched the request",
                details={
                    "method": str(request_context.method),
                    "path": request_context.path,
                },
            )
        return self.resolved_mock
