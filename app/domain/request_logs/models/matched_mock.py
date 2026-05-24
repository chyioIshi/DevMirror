"""Модель с информацией о моке, зарезолвленным для запроса."""

from dataclasses import dataclass
from typing import Any

from app.domain.shared import HttpMethod


@dataclass(slots=True, frozen=True)
class MatchedMock:
    """Описывает найденный мок для запроса в журнале."""

    id: str
    name: str
    path: str
    method: HttpMethod
    scope: str
    response_status_code: int
    response_body: Any | None = None
