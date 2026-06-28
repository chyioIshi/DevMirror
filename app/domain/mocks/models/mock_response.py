"""HTTP response model returned by a mock."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.mocks.exceptions import InvalidMockResponseError
from app.domain.mocks.models.side_effects.side_effect import SideEffect


@dataclass(slots=True, frozen=True)
class MockResponse:
    """HTTP response returned by a mock."""

    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    body: Any | None = None
    side_effects: list[SideEffect] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validates the HTTP status code.

        Raises:
            InvalidMockResponseError: If the status code is outside the valid HTTP
                range.
        """
        if not 100 <= self.status_code <= 599:
            raise InvalidMockResponseError("MockResponse status_code must be in [100, 599]")
        if self.side_effects is None:
            object.__setattr__(self, "side_effects", [])
            return
        if not all(isinstance(side_effect, SideEffect) for side_effect in self.side_effects):
            raise InvalidMockResponseError(
                "MockResponse side_effects must contain SideEffect items"
            )
        object.__setattr__(self, "side_effects", list(self.side_effects))
