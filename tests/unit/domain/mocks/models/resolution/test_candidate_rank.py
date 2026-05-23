from app.domain.mocks.models.resolution import CandidateRank


class TestCandidateRank:
    """Проверяет сортировочный ключ ранга кандидата."""

    def test_sort_key_returns_ranking_fields_in_order(self) -> None:
        """Проверяет, что sort_key возвращает поля ранжирования по порядку."""
        rank = CandidateRank(
            priority=10,
            scope_rank=1,
            specificity=2,
            rule_score=40,
            updated_at=20.0,
            created_at=10.0,
            stable_id="mock-1",
        )

        assert rank.sort_key() == (10, 1, 2, 40, 20.0, 10.0, "mock-1")
