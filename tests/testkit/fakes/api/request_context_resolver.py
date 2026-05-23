from fastapi import Request

from app.domain.request_contexts import RequestContext


class FakeRequestContextResolver:
    """Fake RequestContextResolver для integration-тестов catch-all route."""

    def __init__(self, request_context: RequestContext) -> None:
        self.request_context = request_context
        self.resolve_calls: list[Request] = []

    async def resolve(self, request: Request) -> RequestContext:
        """Возвращает заранее заданный контекст запроса."""
        self.resolve_calls.append(request)
        return self.request_context
