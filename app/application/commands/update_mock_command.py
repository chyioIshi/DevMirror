from dataclasses import dataclass, field
from typing import Final

from app.domain.mocks.models import MatchRule, MockResponse
from app.domain.shared import HttpMethod

UNSET: Final = object()


@dataclass(slots=True, frozen=True)
class UpdateMockCommand:
    """Команда частичного обновления мока."""

    mock_id: str
    name: str | object = field(default=UNSET)
    description: str | None | object = field(default=UNSET)
    path: str | object = field(default=UNSET)
    method: HttpMethod | object = field(default=UNSET)
    priority: int | object = field(default=UNSET)
    scope: str | object = field(default=UNSET)
    match_rules: list[MatchRule] | object = field(default=UNSET)
    response: MockResponse | object = field(default=UNSET)
    tags: list[str] | object = field(default=UNSET)

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
