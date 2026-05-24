"""Модель ожидания для проверки журнала запросов."""

from dataclasses import dataclass

from app.domain.shared import HttpMethod


@dataclass(slots=True, frozen=True)
class RequestLogVerificationExpectation:
    """Описывает ожидания для проверки журнала запросов."""

    path: str
    method: HttpMethod
    expected_count: int | None = None
    matched_mock_id: str | None = None
