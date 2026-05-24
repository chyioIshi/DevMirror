"""Модель правила сопоставления входящего запроса."""

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
    """Условие, которому должен соответствовать запрос."""

    source: MatchSource
    operator: MatchOperator
    expected: Any | None = None
    key: str = ""

    def __post_init__(self) -> None:
        """Проверяет инварианты правила сопоставления.

        Raises:
            InvalidMatchRuleError: Если источник требует ключ, оператор требует expected
                или оператор `in` получил значение неподходящего типа.
        """
        if self.source in _KEY_REQUIRED_SOURCES and not self.key:
            raise InvalidMatchRuleError(f"`key` is required for source `{self.source}`")

        if self.operator != MatchOperator.EXISTS and self.expected is None:
            raise InvalidMatchRuleError("`expected` is required for the selected operator")

        if self.operator == MatchOperator.IN and not isinstance(self.expected, list):
            raise InvalidMatchRuleError("`expected` must be a list for operator `in`")
