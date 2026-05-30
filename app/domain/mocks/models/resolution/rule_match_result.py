"""Rule matching result models for incoming requests."""

from dataclasses import dataclass, field

from app.domain.mocks.models.match_rule import MatchRule


@dataclass(slots=True)
class RuleEvaluation:
    """Result of evaluating one matching rule."""

    rule: MatchRule
    matched: bool
    score: int = 0
    actual: object = None


@dataclass(slots=True)
class RuleMatchResult:
    """Overall result of checking all rules and the final match score."""

    matched: bool
    score: int = 0
    evaluations: list[RuleEvaluation] = field(default_factory=list)
