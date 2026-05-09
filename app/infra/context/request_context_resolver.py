
from fastapi import Request

from app.domain.request_contexts import RequestContext
from app.domain.shared import HttpMethod
from app.infra.request import RequestDataAccessor


class RequestContextResolver:
    """Собирает нормализованный контекст запроса из сырых данных FastAPI."""

    def __init__(self, request_data_accessor: RequestDataAccessor) -> None:
        """Инициализирует резолвер accessor-ом тела запроса."""
        self._request_data_accessor = request_data_accessor

    async def resolve(self, request: Request) -> RequestContext:
        """Преобразует сырой HTTP-запрос в доменную модель контекста."""
        body = await self._request_data_accessor.get_json(request)
        if body is None:
            body = await self._request_data_accessor.get_text(request)

        return RequestContext(
            method=HttpMethod(request.method.upper()),
            path=request.url.path,
            headers=dict(request.headers.items()),
            query_params=self._collect_query_params(request),
            body=body,
        )

    @staticmethod
    def _collect_query_params(request: Request) -> dict[str, str | list[str]]:
        """Собирает query-параметры, сохраняя одиночные и множественные значения."""
        query_params: dict[str, str | list[str]] = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
            query_params[key] = values if len(values) > 1 else values[0]
        return query_params
