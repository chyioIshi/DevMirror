from dataclasses import dataclass, field

from app.domain.mocks.models.resolution.candidate_evaluation import (
    CandidateEvaluation,
)
from app.domain.mocks.models.resolution.resolved_mock import ResolvedMock


@dataclass(slots=True, frozen=True)
class MockResolutionResult:
    """Описывает результат разрешения запроса до мока."""

    requested_scope: str
    resolved_mock: ResolvedMock | None
    evaluations: list[CandidateEvaluation] = field(default_factory=list)

    @property
    def candidate_count(self) -> int:
        """Возвращает количество оцененных кандидатов.
        
        Args:
            None
            
        Returns:
            Количество оцененных кандидатов.
        """
        return len(self.evaluations)

    @property
    def matched_count(self) -> int:
        """Возвращает количество кандидатов, соответствующих правилам запроса.
        
        Args:
            None

        Returns:
            Количество кандидатов, соответствующих правилам запроса.
        """
        return sum(1 for evaluation in self.evaluations if evaluation.matched)
