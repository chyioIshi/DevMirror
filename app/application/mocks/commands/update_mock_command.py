"""Application commands for mock use cases."""

from dataclasses import dataclass, field
from typing import Final

from app.domain.mocks.models import MatchRule, MockResponse
from app.domain.shared import HttpMethod


class UnsetType:
    """Sentinel type for update fields that were not provided."""

    __slots__ = ()


UNSET: Final = UnsetType()


@dataclass(slots=True, frozen=True)
class UpdateMockCommand:
    """Command for partially updating a mock."""

    mock_id: str
    name: str | UnsetType = field(default=UNSET)
    description: str | None | UnsetType = field(default=UNSET)
    path: str | UnsetType = field(default=UNSET)
    method: HttpMethod | UnsetType = field(default=UNSET)
    priority: int | UnsetType = field(default=UNSET)
    scope: str | UnsetType = field(default=UNSET)
    mock_session_id: str | None | UnsetType = field(default=UNSET)
    match_rules: list[MatchRule] | UnsetType = field(default=UNSET)
    response: MockResponse | UnsetType = field(default=UNSET)
    tags: list[str] | UnsetType = field(default=UNSET)

    def has_changes(self) -> bool:
        """Checks whether the command contains at least one updated field.

        Returns:
            True when at least one field was provided; otherwise False.
        """
        return any(
            value is not UNSET
            for value in (
                self.name,
                self.description,
                self.path,
                self.method,
                self.priority,
                self.scope,
                self.mock_session_id,
                self.match_rules,
                self.response,
                self.tags,
            )
        )
