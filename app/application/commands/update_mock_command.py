from dataclasses import dataclass, field
from typing import Final

from app.domain.mocks.models import MatchRule, MockResponse
from app.domain.shared import HttpMethod


class UnsetType:
    __slots__ = ()


UNSET: Final = UnsetType()


@dataclass(slots=True, frozen=True)
class UpdateMockCommand:
    """Команда частичного обновления мока."""

    mock_id: str
    name: str | UnsetType = field(default=UNSET)
    description: str | None | UnsetType = field(default=UNSET)
    path: str | UnsetType = field(default=UNSET)
    method: HttpMethod | UnsetType = field(default=UNSET)
    priority: int | UnsetType = field(default=UNSET)
    scope: str | UnsetType = field(default=UNSET)
    match_rules: list[MatchRule] | UnsetType = field(default=UNSET)
    response: MockResponse | UnsetType = field(default=UNSET)
    tags: list[str] | UnsetType = field(default=UNSET)

    def has_changes(self) -> bool:
        """Проверяет, содержит ли команда хотя бы одно изменяемое поле."""
        return any(
            value is not UNSET
            for value in (
                self.name,
                self.description,
                self.path,
                self.method,
                self.priority,
                self.scope,
                self.match_rules,
                self.response,
                self.tags,
            )
        )
