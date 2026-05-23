from app.domain.mocks.models.resolution import CandidateEvaluation, RuleMatchResult


class TestCandidateEvaluation:
    """Проверяет оценку кандидата на резолвинг запроса."""

    def test_matched_reflects_rule_match_result(self, mock_factory) -> None:
        """Проверяет, что matched берется из rule_result (RuleMatchResult)."""
        evaluation = CandidateEvaluation(
            mock=mock_factory.create_mock(),
            rule_result=RuleMatchResult(matched=True),
        )

        assert evaluation.matched is True
