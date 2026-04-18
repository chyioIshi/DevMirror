from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.resolution.candidate_rank import CandidateRank
from app.domain.mocks.models.resolution.rule_match_result import RuleMatchResult


class MockSelectionPolicy:
    """Определяет правила ранжирования и сортировки подходящих моков."""

    def rank_candidate(
        self,
        mock: Mock,
        *,
        requested_scope: str,
        rule_result: RuleMatchResult,
    ) -> CandidateRank:
        """Формирует объект ранга для подходящего кандидата."""
        return CandidateRank(
            priority=mock.priority,
            scope_rank=1 if mock.scope == requested_scope else 0,
            specificity=len(mock.match_rules),
            rule_score=rule_result.score,
            updated_at=mock.updated_at.timestamp(),
            created_at=mock.created_at.timestamp(),
            stable_id=mock.id or "",
        )
