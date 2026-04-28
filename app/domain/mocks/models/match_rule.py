from dataclasses import dataclass
from typing import Any

from app.domain.mocks.exceptions import MockInvariantError
from app.domain.shared.enums import MatchOperator, MatchSource

_KEY_REQUIRED_SOURCES: frozenset[MatchSource] = frozenset({
    MatchSource.HEADER,
    MatchSource.QUERY,
    MatchSource.BODY_JSON,
})


@dataclass(slots=True, frozen=True)
class MatchRule:
    """Условие, которому должен соответствовать запрос."""

    source: MatchSource
    operator: MatchOperator
    expected: Any | None = None
    key: str = ""

    def __post_init__(self) -> None:
        if self.source in _KEY_REQUIRED_SOURCES and not self.key:
            raise MockInvariantError(f"`key` is required for source `{self.source}`")

        if self.operator != MatchOperator.EXISTS and self.expected is None:
            raise MockInvariantError("`expected` is required for the selected operator")

        if self.operator == MatchOperator.IN and not isinstance(self.expected, list):
            raise MockInvariantError("`expected` must be a list for operator `in`")
