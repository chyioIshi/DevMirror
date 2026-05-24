"""Модель ранга кандидата для выбора наиболее подходящего мока."""

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

    def sort_key(self) -> tuple[int, int, int, int, float, float, str]:
        """Возвращает ключ сортировки для ранжированных кандидатов."""
        return (
            self.priority,
            self.scope_rank,
            self.specificity,
            self.rule_score,
            self.updated_at,
            self.created_at,
            self.stable_id,
        )
