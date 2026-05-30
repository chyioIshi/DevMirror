"""MongoDB documents used to persist request log records."""

from datetime import UTC, datetime
from typing import Any

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import DESCENDING

from app.domain.shared import HttpMethod


class RequestContextDocument(BaseModel):
    """Nested Mongo document describing request context data."""

    id: str
    method: HttpMethod
    path: str
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, Any] = Field(default_factory=dict)
    body: Any = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))


class MatchedMockDocument(BaseModel):
    """Nested Mongo document describing the mock matched to a request."""

    id: str
    name: str
    path: str
    method: HttpMethod
    scope: str
    response_status_code: int
    response_body: Any | None = None


class RequestLogDocument(Document):
    """Mongo document used to persist request log records."""

    request_context: RequestContextDocument
    matched_mock: MatchedMockDocument | None = None
    scope: str | None = None
    response_status_code: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    class Settings:
        """Beanie collection settings for request logs."""

        name: str = "request_logs"
        indexes: list[list[tuple[str, int]]] = [
            [("created_at", DESCENDING)],
            [
                ("request_context.path", DESCENDING),
                ("request_context.method", DESCENDING),
                ("created_at", DESCENDING),
            ],
        ]
