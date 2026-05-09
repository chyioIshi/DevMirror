from app.domain.request_contexts import RequestContext


class HeaderScopeResolutionStrategy:
    """Определяет scope из указанного заголовка запроса."""

    def __init__(self, header_name: str) -> None:
        self._header_name = header_name

    async def resolve(self, request_context: RequestContext) -> str | None:
        """Читает значение scope из настроенного заголовка запроса."""
        header_value = request_context.headers.get(self._header_name)
        if header_value in (None, ""):
            return None
        return header_value


class JsonBodyFieldScopeResolutionStrategy:
    """Определяет scope по полю в JSON-теле запроса."""

    def __init__(self, field_name: str) -> None:
        self._field_name = field_name

    async def resolve(self, request_context: RequestContext) -> str | None:
        """Извлекает значение scope из настроенного поля JSON-тела."""
        body = request_context.body
        if not isinstance(body, dict):
            return None

        candidate = body.get(self._field_name)
        if candidate in (None, ""):
            return None
        return str(candidate)


class DefaultScopeResolutionStrategy:
    """Всегда возвращает заранее заданный scope по умолчанию."""

    def __init__(self, default_scope: str) -> None:
        self._default_scope = default_scope

    async def resolve(self, request_context: RequestContext) -> str | None:  # noqa: ARG002
        """Возвращает настроенный scope по умолчанию."""
        return self._default_scope
