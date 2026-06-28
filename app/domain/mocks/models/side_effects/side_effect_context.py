"""Plain data context available to side effect templates."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Self
from uuid import UUID

from app.domain.mocks.exceptions import InvalidSideEffectError
from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.mock_response import MockResponse
from app.domain.request_contexts import RequestContext


@dataclass(slots=True, frozen=True)
class SideEffectContext:
    """Serializable data available while rendering side effect templates."""

    request: dict[str, Any] = field(default_factory=dict)
    mock: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, dict[str, Any]]:
        """Returns the context as a mapping."""
        return {
            "request": self.request,
            "mock": self.mock,
            "response": self.response,
            "execution": self.execution,
        }

    @classmethod
    def from_domain(
        cls,
        *,
        request: RequestContext,
        mock: Mock,
        response: MockResponse,
        execution: dict[str, Any] | None = None,
    ) -> Self:
        """Builds a side effect context from domain models."""
        return cls(
            request=cls._to_plain_data(
                {
                    "id": request.id,
                    "method": request.method,
                    "path": request.path,
                    "headers": {key.lower(): value for key, value in request.headers.items()},
                    "query": request.query_params,
                    "body": request.body,
                    "timestamp": request.timestamp,
                }
            ),
            mock=cls._to_plain_data(
                {
                    "id": mock.id,
                    "name": mock.name,
                    "path": mock.path,
                    "method": mock.method,
                    "priority": mock.priority,
                    "scope": mock.scope,
                    "tags": mock.tags,
                }
            ),
            response=cls._to_plain_data(
                {
                    "status_code": response.status_code,
                    "headers": response.headers,
                    "body": response.body,
                }
            ),
            execution=cls._to_plain_data(execution or {}),
        )

    @classmethod
    def _to_plain_data(cls, value: Any) -> Any:
        if value is None or isinstance(value, bool | int | float | str):
            return value
        if isinstance(value, dict):
            return {str(key): cls._to_plain_data(item) for key, item in value.items()}
        if isinstance(value, list | tuple):
            return [cls._to_plain_data(item) for item in value]
        if isinstance(value, StrEnum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)

        raise InvalidSideEffectError(
            "SideEffectContext must contain only plain serializable data",
            details={"value_type": type(value).__name__},
        )
