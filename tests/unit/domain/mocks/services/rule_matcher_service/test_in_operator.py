import pytest

from app.domain.shared import MatchOperator, MatchSource

ALLOWED_ROLES = ["admin", "editor"]


class TestInOperator:
    """Проверяет оператор IN."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "header_value,should_match",
        [
            ("admin", True),
            ("editor", True),
            ("viewer", False),
            ("", False),
        ],
    )
    async def test_header_single_value(
        self,
        request_factory,
        matcher,
        mock_factory,
        header_value,
        should_match,
    ) -> None:
        """Проверяет значение header в списке допустимых."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.IN,
            expected=ALLOWED_ROLES,
            key="role",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers={"role": header_value}),
            [rule],
        )

        assert result.matched is should_match

    @pytest.mark.asyncio
    async def test_absent_header_does_not_match(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет, что отсутствующий header не совпадает."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.IN,
            expected=ALLOWED_ROLES,
            key="x-role",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(),
            [rule],
        )

        assert result.matched is False

    @pytest.mark.asyncio
    async def test_match_contributes_positive_score(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет, что совпадение дает положительный score."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.IN,
            expected=ALLOWED_ROLES,
            key="role",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers={"role": "admin"}),
            [rule],
        )

        assert result.score > 0
