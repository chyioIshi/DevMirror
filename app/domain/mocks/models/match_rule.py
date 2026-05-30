"""Request matching rule model."""

from dataclasses import dataclass
from typing import Any

from app.domain.mocks.exceptions import InvalidMatchRuleError
from app.domain.shared import MatchOperator, MatchSource

_KEY_REQUIRED_SOURCES: frozenset[MatchSource] = frozenset(
    {
        MatchSource.HEADER,
        MatchSource.QUERY,
        MatchSource.BODY_JSON,
    }
)


@dataclass(slots=True, frozen=True)
class MatchRule:
    """Rule that an incoming request must satisfy."""

    source: MatchSource
    operator: MatchOperator
    expected: Any | None = None
    key: str = ""

    def __post_init__(self) -> None:
        """Validates match rule invariants.

        Raises:
            InvalidMatchRuleError: If the source requires a key, the operator requires
                an expected value, or the `in` operator receives a value of the wrong
                type.
        """
        if self.source in _KEY_REQUIRED_SOURCES and not self.key:
            raise InvalidMatchRuleError(f"`key` is required for source `{self.source}`")

        if self.operator != MatchOperator.EXISTS and self.expected is None:
            raise InvalidMatchRuleError("`expected` is required for the selected operator")

        if self.operator == MatchOperator.IN and not isinstance(self.expected, list):
            raise InvalidMatchRuleError("`expected` must be a list for operator `in`")
