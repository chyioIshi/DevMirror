"""Filter model for listing mocks."""

from dataclasses import dataclass

from app.domain.shared import HttpMethod


@dataclass(slots=True, frozen=True)
class MockListFilters:
    """Optional filters for retrieving a list of mocks."""

    path: str | None = None
    method: HttpMethod | None = None
    active: bool | None = None
    scope: str | None = None
