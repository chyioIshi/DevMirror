"""Candidate evaluation model used during mock resolution."""

from dataclasses import dataclass

from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.resolution.candidate_rank import CandidateRank
from app.domain.mocks.models.resolution.rule_match_result import RuleMatchResult


@dataclass(slots=True, frozen=True)
class CandidateEvaluation:
    """Result of evaluating one candidate against an incoming request."""

    mock: Mock
    rule_result: RuleMatchResult
    rank: CandidateRank | None = None

    @property
    def matched(self) -> bool:
        """Returns whether the candidate mock matched the request.

        Returns:
            True when the candidate mock matched the request; otherwise False.
        """
        return self.rule_result.matched
