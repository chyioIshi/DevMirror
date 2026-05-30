"""Infrastructure scope resolution strategies."""

from app.domain.request_contexts import RequestContext


class HeaderScopeResolutionStrategy:
    """Resolves scope from a configured request header."""

    def __init__(self, header_name: str) -> None:
        """Initializes the strategy with a header name.

        Args:
            header_name: Header used as scope source.
        """
        self._header_name = header_name

    async def resolve(self, request_context: RequestContext) -> str | None:
        """Reads scope from the configured request header.

        Args:
            request_context: Incoming request context.

        Returns:
            Header value or ``None`` when the header is missing or empty.
        """
        header_value = request_context.headers.get(self._header_name)
        if header_value in (None, ""):
            return None
        return header_value


class JsonBodyFieldScopeResolutionStrategy:
    """Resolves scope from a field in the JSON request body."""

    def __init__(self, field_name: str) -> None:
        """Initializes the strategy with a JSON field name.

        Args:
            field_name: JSON body field used as scope source.
        """
        self._field_name = field_name

    async def resolve(self, request_context: RequestContext) -> str | None:
        """Extracts scope from the configured JSON body field.

        Args:
            request_context: Incoming request context.

        Returns:
            Field value converted to string or ``None`` when unavailable.
        """
        body = request_context.body
        if not isinstance(body, dict):
            return None

        candidate = body.get(self._field_name)
        if candidate in (None, ""):
            return None
        return str(candidate)


class DefaultScopeResolutionStrategy:
    """Always returns a configured default scope."""

    def __init__(self, default_scope: str) -> None:
        """Initializes the strategy with a default scope.

        Args:
            default_scope: Scope returned by the strategy.
        """
        self._default_scope = default_scope

    async def resolve(self, request_context: RequestContext) -> str | None:  # noqa: ARG002
        """Returns the configured default scope.

        Args:
            request_context: Incoming request context, unused by this strategy.

        Returns:
            Configured default scope.
        """
        return self._default_scope
