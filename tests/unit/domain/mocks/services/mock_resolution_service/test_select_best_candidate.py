import pytest

from app.domain.mocks.models.resolution import CandidateEvaluation, CandidateRank, RuleMatchResult


class TestSelectBestCandidate:
    """Проверяет выбор наиболее подходящего кандидата
    (CandidateEvaluation) для запроса."""

    def test_returns_none_when_no_candidates_match(
        self,
        mock_resolution_service,
        mock_factory,
    ) -> None:
        """Проверяет, что без совпадений результат отсутствует."""
        result = mock_resolution_service.select_best_candidate(
            [
                CandidateEvaluation(
                    mock=mock_factory.create_mock(),
                    rule_result=RuleMatchResult(matched=False),
                ),
            ],
            requested_scope="global",
        )

        assert result is None

    def test_returns_candidate_with_highest_rank(
        self,
        mock_resolution_service,
        mock_factory,
    ) -> None:
        """Проверяет, что выбирается кандидат с лучшим rank."""
        low = mock_factory.create_mock(mock_id="low", name="low")
        high = mock_factory.create_mock(mock_id="high", name="high")
        result = mock_resolution_service.select_best_candidate(
            [
                CandidateEvaluation(
                    mock=low,
                    rule_result=RuleMatchResult(matched=True),
                    rank=CandidateRank(1, 1, 0, 0, 0.0, 0.0, "low"),
                ),
                CandidateEvaluation(
                    mock=high,
                    rule_result=RuleMatchResult(matched=True),
                    rank=CandidateRank(10, 1, 0, 0, 0.0, 0.0, "high"),
                ),
            ],
            requested_scope="user-a",
        )

        assert result is not None
        assert result.mock == high
        assert result.scope == "user-a"

    def test_raises_when_matched_candidate_has_no_rank(
        self,
        mock_resolution_service,
        mock_factory,
    ) -> None:
        """Проверяет защиту от совпавшей оценки без rank."""
        with pytest.raises(ValueError, match="Matched candidate evaluation"):
            mock_resolution_service.select_best_candidate(
                [
                    CandidateEvaluation(
                        mock=mock_factory.create_mock(),
                        rule_result=RuleMatchResult(matched=True),
                    ),
                ],
                requested_scope="global",
            )
