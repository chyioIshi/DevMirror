"""HTTP response model returned by a mock."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.mocks.exceptions import InvalidMockResponseError


@dataclass(slots=True, frozen=True)
class MockResponse:
    """HTTP response returned by a mock."""

    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    body: Any | None = None

    def __post_init__(self) -> None:
        """Validates the HTTP status code.

        Raises:
            InvalidMockResponseError: If the status code is outside the valid HTTP
                range.
        """
        if not 100 <= self.status_code <= 599:
            raise InvalidMockResponseError("MockResponse status_code must be in [100, 599]")
