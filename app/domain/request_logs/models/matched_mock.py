"""Model with information about a mock matched to a request."""

from dataclasses import dataclass
from typing import Any

from app.domain.shared import HttpMethod


@dataclass(slots=True, frozen=True)
class MatchedMock:
    """Describes a mock matched to a request in the log."""

    id: str
    name: str
    path: str
    method: HttpMethod
    scope: str
    response_status_code: int
    response_body: Any | None = None
