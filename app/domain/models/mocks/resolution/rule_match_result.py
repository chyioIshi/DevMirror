
from dataclasses import dataclass, field

from app.domain.models.mocks.match_rule import MatchRule


@dataclass(slots=True)
class RuleEvaluation:
    """Хранит результат вычисления одного правила сопоставления."""

    rule: MatchRule
    matched: bool
    score: int = 0
    actual: object = None


@dataclass(slots=True)
class RuleMatchResult:
    """Описывает общий результат проверки всех правил
    и хранит итоговый score сопоставления."""

    matched: bool
    score: int = 0
    evaluations: list[RuleEvaluation] = field(default_factory=list)
