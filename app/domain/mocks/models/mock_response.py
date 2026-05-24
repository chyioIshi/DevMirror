"""Модель HTTP-ответа, который возвращает мок."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.mocks.exceptions import InvalidMockResponseError


@dataclass(slots=True, frozen=True)
class MockResponse:
    """HTTP-ответ, который возвращает мок."""

    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    body: Any | None = None

    def __post_init__(self) -> None:
        """Проверяет корректность HTTP status code.

        Raises:
            InvalidMockResponseError: Если status code находится вне допустимого HTTP-диапазона.
        """
        if not 100 <= self.status_code <= 599:
            raise InvalidMockResponseError("MockResponse status_code must be in [100, 599]")
