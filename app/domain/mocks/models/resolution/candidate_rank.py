"""Candidate ranking model used to choose the best mock."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CandidateRank:
    """Ranking metrics for a mock candidate."""

    priority: int
    scope_rank: int
    specificity: int
    rule_score: int
    updated_at: float
    created_at: float
    stable_id: str

    def sort_key(self) -> tuple[int, int, int, int, float, float, str]:
        """Returns the sort key for ranked candidates.

        Returns:
            Tuple used to compare candidate ranks.
        """
        return (
            self.priority,
            self.scope_rank,
            self.specificity,
            self.rule_score,
            self.updated_at,
            self.created_at,
            self.stable_id,
        )
