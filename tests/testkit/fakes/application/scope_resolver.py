from app.domain.request_contexts import RequestContext


class FakeScopeResolver:
    """Fake ScopeResolver с явно заданным scope."""

    def __init__(self, scope: str = "user-a") -> None:
        self.scope = scope
        self.resolved_contexts: list[RequestContext] = []

    async def resolve_scope(self, request_context: RequestContext) -> str:
        """Возвращает заданный scope."""
        self.resolved_contexts.append(request_context)
        return self.scope
