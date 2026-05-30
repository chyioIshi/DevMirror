"""Selected mock model and its resolution metadata."""

from dataclasses import dataclass

from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.resolution.rule_match_result import RuleMatchResult


@dataclass(slots=True)
class ResolvedMock:
    """Selected mock and metadata describing its resolution."""

    mock: Mock
    scope: str
    rule_result: RuleMatchResult
