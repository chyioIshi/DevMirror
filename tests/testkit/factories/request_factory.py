from typing import Any
from urllib.parse import parse_qs

from starlette.requests import Request

from app.domain.request_contexts import RequestContext
from app.domain.shared import HttpMethod


class RequestFactory:
    """Создает RequestContext со значениями по умолчанию."""

    def create_request_context(
        self,
        *,
        method: str = "GET",
        path: str = "/test",
        headers: dict[str, str] | None = None,
        query_string: str = "",
        query_params: dict[str, Any] | None = None,
        body: Any = None,
    ) -> RequestContext:
        return RequestContext(
            method=HttpMethod(method.upper()),
            path=path,
            headers=headers or {},
            query_params=query_params or self._query_params_from(query_string),
            body=body,
        )

    def create_starlette_request(
        self,
        *,
        method: str = "GET",
        path: str = "/test",
        headers: dict[str, str] | None = None,
        query_string: str = "",
    ) -> Request:
        """Создает Starlette Request с указанными полями или значениями по умолчанию."""
        raw_headers = [
            (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
        ]
        scope: dict[str, Any] = {
            "type": "http",
            "method": method,
            "path": path,
            "headers": raw_headers,
            "query_string": query_string.encode(),
        }
        return Request(scope)

    def _query_params_from(self, query_string: str) -> dict[str, str | list[str]]:
        """Преобразует строку запроса в словарь параметров."""
        params_raw = parse_qs(query_string)
        return {
            key: values[0] if len(values) == 1 else values for key, values in params_raw.items()
        }
