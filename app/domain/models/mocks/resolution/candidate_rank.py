
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CandidateRank:
    """Хранит метрики ранжирования для кандидата в моки."""

    priority: int
    scope_rank: int
    specificity: int
    rule_score: int
    updated_at: float
    created_at: float
    stable_id: str
