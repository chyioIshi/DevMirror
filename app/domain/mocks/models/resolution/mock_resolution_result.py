"""Final mock resolution result model for a request."""

from dataclasses import dataclass, field

from app.domain.mocks.models.resolution.candidate_evaluation import (
    CandidateEvaluation,
)
from app.domain.mocks.models.resolution.resolved_mock import ResolvedMock


@dataclass(slots=True, frozen=True)
class MockResolutionResult:
    """Result of resolving a request to a mock."""

    requested_scope: str
    resolved_mock: ResolvedMock | None
    evaluations: list[CandidateEvaluation] = field(default_factory=list)

    @property
    def candidate_count(self) -> int:
        """Returns the number of evaluated candidates.

        Returns:
            Number of evaluated candidates.
        """
        return len(self.evaluations)

    @property
    def matched_count(self) -> int:
        """Returns the number of candidates matched by request rules.

        Returns:
            Number of candidates matched by request rules.
        """
        return sum(1 for evaluation in self.evaluations if evaluation.matched)
