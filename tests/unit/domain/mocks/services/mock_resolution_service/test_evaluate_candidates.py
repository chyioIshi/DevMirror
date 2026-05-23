import pytest

from app.domain.shared import MatchOperator, MatchSource


class TestEvaluateCandidates:
    """Проверяет оценку кандидатов на соответствие запросу."""

    @pytest.mark.asyncio
    async def test_adds_rank_only_for_matched_candidates(
        self,
        mock_resolution_service,
        mock_factory,
        request_factory,
    ) -> None:
        """Проверяет, что rank есть только у совпавшего кандидата."""
        matching_rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            key="x-plan",
            operator=MatchOperator.EQ,
            expected="premium",
        )
        matched = mock_factory.create_mock(
            name="matched",
            match_rules=[matching_rule],
        )
        unmatched = mock_factory.create_mock(
            name="unmatched",
            match_rules=[
                mock_factory.match_rule(
                    source=MatchSource.HEADER,
                    key="x-plan",
                    operator=MatchOperator.EQ,
                    expected="basic",
                ),
            ],
        )

        evaluations = await mock_resolution_service.evaluate_candidates(
            request_context=request_factory.create_request_context(
                headers={"x-plan": "premium"},
            ),
            candidates=[matched, unmatched],
            requested_scope="global",
        )

        assert evaluations[0].matched is True
        assert evaluations[0].rank is not None
        assert evaluations[1].matched is False
        assert evaluations[1].rank is None
