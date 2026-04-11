
from fastapi import Request

from app.domain.services.request_data_accessor import RequestDataAccessor


class HeaderScopeResolutionStrategy:
    """Определяет scope из указанного заголовка запроса."""

    def __init__(self, header_name: str) -> None:
        """Сохраняет имя заголовка, из которого нужно брать scope."""
        self._header_name = header_name

    async def resolve(self, request: Request) -> str | None:
        """Читает значение scope из настроенного заголовка запроса."""
        header_value = request.headers.get(self._header_name)
        if header_value in (None, ""):
            return None
        return header_value


class JsonBodyFieldScopeResolutionStrategy:
    """Определяет scope по полю в JSON-теле запроса."""

    def __init__(self, request_data_accessor: RequestDataAccessor, field_name: str) -> None:
        """Сохраняет accessor и имя JSON-поля для поиска scope."""
        self._request_data_accessor = request_data_accessor
        self._field_name = field_name

    async def resolve(self, request: Request) -> str | None:
        """Извлекает значение scope из настроенного поля JSON-тела."""
        body = await self._request_data_accessor.get_json(request)
        if not isinstance(body, dict):
            return None

        candidate = body.get(self._field_name)
        if candidate in (None, ""):
            return None

        return str(candidate)


class DefaultScopeResolutionStrategy:
    """Всегда возвращает заранее заданный scope по умолчанию."""

    def __init__(self, default_scope: str) -> None:
        """Сохраняет scope по умолчанию, возвращаемый стратегией."""
        self._default_scope = default_scope

    async def resolve(self, request: Request) -> str | None:
        """Возвращает настроенный scope по умолчанию."""
        return self._default_scope