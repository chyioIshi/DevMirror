from dataclasses import dataclass

from app.domain.shared.enums import HttpMethod


@dataclass(slots=True, frozen=True)
class MockListFilters:
    """Описывает необязательные фильтры для получения списка моков."""

    path: str | None = None
    method: HttpMethod | None = None
    active: bool | None = None
    scope: str | None = None
