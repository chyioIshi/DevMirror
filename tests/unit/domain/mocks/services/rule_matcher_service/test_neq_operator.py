import pytest

from app.domain.shared import MatchOperator, MatchSource


class TestNeqOperator:
    """Проверяет оператор NEQ."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "header_value,expected,should_match",
        [
            ("staging", "prod", True),
            ("prod", "prod", False),
            ("", "prod", True),
        ],
    )
    async def test_header(
        self,
        request_factory,
        matcher,
        mock_factory,
        header_value,
        expected,
        should_match,
    ) -> None:
        """Проверяет неравенство значения header."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.NEQ,
            expected=expected,
            key="env",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers={"env": header_value}),
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
        """Проверяет, что отсутствующий header не считается неравным."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.NEQ,
            expected="prod",
            key="x-env",
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
            operator=MatchOperator.NEQ,
            expected="prod",
            key="env",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers={"env": "staging"}),
            [rule],
        )

        assert result.score > 0
