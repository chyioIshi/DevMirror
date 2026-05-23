from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.request_contexts import RequestContext
from app.domain.request_logs.models.matched_mock import MatchedMock
from app.domain.request_logs.models.verification.expectation import (
    RequestLogVerificationExpectation,
)


@dataclass(slots=True)
class RequestLogRecord:
    """Описывает одну запись журнала входящего запроса."""

    request_context: RequestContext
    id: str | None = None
    matched_mock: MatchedMock | None = None
    scope: str | None = None
    response_status_code: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def matches_expectation(
        self,
        expectation: RequestLogVerificationExpectation,
    ) -> bool:
        """Проверяет, соответствует ли запись ожиданиям."""
        if self.request_context.path != expectation.path:
            return False
        if self.request_context.method != expectation.method:
            return False
        if expectation.matched_mock_id is not None:
            return (
                self.matched_mock is not None
                and self.matched_mock.id == expectation.matched_mock_id
            )
        return True
