import pytest

from app.domain.shared import MatchOperator, MatchSource


class TestResolveBest:
    """Проверяет резолвинг лучшего кандидата."""

    @pytest.mark.asyncio
    async def test_selects_highest_priority_matching_candidate(
        self,
        mock_resolution_service,
        mock_factory,
        request_factory,
    ) -> None:
        """Проверяет, что выбирается совпавший кандидат с большим priority."""
        low_priority = mock_factory.create_mock(
            mock_id="low-priority",
            name="low-priority",
            path="/users",
            priority=1,
            active=True,
        )
        high_priority = mock_factory.create_mock(
            mock_id="high-priority",
            name="high-priority",
            path="/users",
            priority=10,
            active=True,
        )

        result = await mock_resolution_service.resolve_best(
            request_context=request_factory.create_request_context(path="/users"),
            candidates=[low_priority, high_priority],
            requested_scope="global",
        )

        assert result.resolved_mock is not None
        assert result.resolved_mock.mock == high_priority
        assert result.candidate_count == 2
        assert result.matched_count == 2

    @pytest.mark.asyncio
    async def test_prefers_requested_scope_over_fallback_scope(
        self,
        mock_resolution_service,
        mock_factory,
        request_factory,
    ) -> None:
        """Проверяет, что точный scope побеждает global scope."""
        fallback = mock_factory.create_mock(
            mock_id="fallback",
            name="fallback",
            path="/users",
            scope="global",
            active=True,
        )
        scoped = mock_factory.create_mock(
            mock_id="scoped",
            name="scoped",
            path="/users",
            scope="user-a",
            active=True,
        )

        result = await mock_resolution_service.resolve_best(
            request_context=request_factory.create_request_context(path="/users"),
            candidates=[fallback, scoped],
            requested_scope="user-a",
        )

        assert result.resolved_mock is not None
        assert result.resolved_mock.mock == scoped
        assert result.resolved_mock.scope == "user-a"

    @pytest.mark.asyncio
    async def test_ignores_candidates_with_unmatched_rules(
        self,
        mock_resolution_service,
        mock_factory,
        request_factory,
    ) -> None:
        """Проверяет, что кандидат с неподходящими правилами не выбирается."""
        premium_rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            key="x-plan",
            operator=MatchOperator.EQ,
            expected="premium",
        )
        unmatched_high_priority = mock_factory.create_mock(
            mock_id="unmatched-high-priority",
            name="unmatched-high-priority",
            path="/users",
            priority=100,
            active=True,
            match_rules=[premium_rule],
        )
        matched_low_priority = mock_factory.create_mock(
            mock_id="matched-low-priority",
            name="matched-low-priority",
            path="/users",
            priority=1,
            active=True,
        )

        result = await mock_resolution_service.resolve_best(
            request_context=request_factory.create_request_context(
                path="/users",
                headers={"x-plan": "basic"},
            ),
            candidates=[unmatched_high_priority, matched_low_priority],
            requested_scope="global",
        )

        assert result.resolved_mock is not None
        assert result.resolved_mock.mock == matched_low_priority
        assert result.candidate_count == 2
        assert result.matched_count == 1
