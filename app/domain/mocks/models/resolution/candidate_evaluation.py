from dataclasses import dataclass

from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.resolution.candidate_rank import CandidateRank
from app.domain.mocks.models.resolution.rule_match_result import RuleMatchResult


@dataclass(slots=True, frozen=True)
class CandidateEvaluation:
    """Описывает результат оценки одного кандидата на соответствие входящему запросу."""

    mock: Mock
    rule_result: RuleMatchResult
    rank: CandidateRank | None = None

    @property
    def matched(self) -> bool:
        """Возвращает результат соответствия мока-кандидата запросу.

        Args:
            None

        Returns:
            True, если мок-кандидат соответствует запросу, иначе False.
        """
        return self.rule_result.matched
