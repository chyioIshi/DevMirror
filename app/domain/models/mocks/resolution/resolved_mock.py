
from dataclasses import dataclass

from app.domain.models.mocks.mock import Mock
from app.domain.models.mocks.resolution.rule_match_result import RuleMatchResult


@dataclass(slots=True)
class ResolvedMock:
    """Хранит выбранный мок и метаданные его разрешения."""

    mock: Mock
    scope: str
    rule_result: RuleMatchResult
