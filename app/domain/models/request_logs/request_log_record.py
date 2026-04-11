
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.context.request_context import RequestContext
from app.domain.models.request_logs.matched_mock import MatchedMock


class RequestLogRecord(BaseModel):
    """Описывает одну запись журнала входящего запроса."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    request_context: RequestContext
    matched_mock: MatchedMock | None = None
    scope: str | None = None
    response_status_code: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
