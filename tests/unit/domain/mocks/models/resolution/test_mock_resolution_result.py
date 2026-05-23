from app.domain.mocks.models.resolution import (
    CandidateEvaluation,
    MockResolutionResult,
    RuleMatchResult,
)


class TestMockResolutionResult:
    """Проверяет результат резолвинга мока."""

    def test_counts_candidates_and_matches(self, mock_factory) -> None:
        """Проверяет счетчики всех и совпавших кандидатов."""
        result = MockResolutionResult(
            requested_scope="user-a",
            resolved_mock=None,
            evaluations=[
                CandidateEvaluation(
                    mock=mock_factory.create_mock(name="matched"),
                    rule_result=RuleMatchResult(matched=True),
                ),
                CandidateEvaluation(
                    mock=mock_factory.create_mock(name="unmatched"),
                    rule_result=RuleMatchResult(matched=False),
                ),
            ],
        )

        assert result.candidate_count == 2
        assert result.matched_count == 1
