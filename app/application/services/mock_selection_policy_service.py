
from app.domain.models.mocks.mock import Mock
from app.domain.models.mocks.resolution.candidate_rank import CandidateRank
from app.domain.models.mocks.resolution.rule_match_result import RuleMatchResult


class MockSelectionPolicyService:
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

    def sort_key(self, rank: CandidateRank) -> tuple[int, int, int, int, float, float, str]:
        """Возвращает ключ сортировки для ранжированных кандидатов."""
        return (
            rank.priority,
            rank.scope_rank,
            rank.specificity,
            rank.rule_score,
            rank.updated_at,
            rank.created_at,
            rank.stable_id,
        )
