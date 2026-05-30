"""Policy for ranking mock candidates."""

from app.domain.mocks.models import Mock
from app.domain.mocks.models.resolution import CandidateRank, RuleMatchResult


class MockSelectionPolicy:
    """Defines ranking and sorting rules for matching mocks."""

    def rank_candidate(
        self,
        mock: Mock,
        *,
        requested_scope: str,
        rule_result: RuleMatchResult,
    ) -> CandidateRank:
        """Builds a rank object for a matching candidate.

        Args:
            mock: Matching mock candidate.
            requested_scope: Scope requested for resolution.
            rule_result: Result of matching the candidate rules.

        Returns:
            Candidate rank used for sorting.
        """
        return CandidateRank(
            priority=mock.priority,
            scope_rank=1 if mock.scope == requested_scope else 0,
            specificity=len(mock.match_rules),
            rule_score=rule_result.score,
            updated_at=mock.updated_at.timestamp(),
            created_at=mock.created_at.timestamp(),
            stable_id=mock.id or "",
        )
