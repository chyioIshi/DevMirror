"""Модель выбранного мока и метаданных разрешения."""

from dataclasses import dataclass

from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.resolution.rule_match_result import RuleMatchResult


@dataclass(slots=True)
class ResolvedMock:
    """Хранит выбранный мок и метаданные его разрешения."""

    mock: Mock
    scope: str
    rule_result: RuleMatchResult
