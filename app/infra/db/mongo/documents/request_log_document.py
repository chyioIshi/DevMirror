
from datetime import UTC, datetime

from beanie import Document
from pydantic import Field
from pymongo import DESCENDING

from app.domain.request_contexts.models.request_context import RequestContext
from app.domain.request_logs.models.matched_mock import MatchedMock


class RequestLogDocument(Document):
    """Mongo-документ для хранения записи журнала запросов."""

    request_context: RequestContext
    matched_mock: MatchedMock | None = None
    scope: str | None = None
    response_status_code: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    class Settings:
        """Настройки коллекции Beanie и индексы журнала запросов."""

        name: str = "request_logs"
        indexes: list[list[tuple[str, int]]] = [
            [("created_at", DESCENDING)],
            [
                ("request_context.path", DESCENDING),
                ("request_context.method", DESCENDING),
                ("created_at", DESCENDING),
            ],
        ]
