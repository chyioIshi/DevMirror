import pytest

from app.domain.shared import MatchOperator, MatchSource


class TestExistsOperator:
    """Проверяет оператор EXISTS."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "headers,should_match",
        [
            ({"authorization": "Bearer token"}, True),
            ({}, False),
        ],
    )
    async def test_header(
        self,
        request_factory,
        matcher,
        mock_factory,
        headers,
        should_match,
    ) -> None:
        """Проверяет наличие header."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.EXISTS,
            expected="any",
            key="authorization",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers=headers),
            [rule],
        )

        assert result.matched is should_match

    @pytest.mark.asyncio
    async def test_query_param_present(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет наличие query-параметра."""
        rule = mock_factory.match_rule(
            source=MatchSource.QUERY,
            operator=MatchOperator.EXISTS,
            expected="any",
            key="debug",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(query_string="debug=true"),
            [rule],
        )

        assert result.matched is True

    @pytest.mark.asyncio
    async def test_query_param_absent(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет отсутствие query-параметра."""
        rule = mock_factory.match_rule(
            source=MatchSource.QUERY,
            operator=MatchOperator.EXISTS,
            expected="any",
            key="debug",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(),
            [rule],
        )

        assert result.matched is False

    @pytest.mark.asyncio
    async def test_body_json_field_present(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет наличие поля в json body."""
        rule = mock_factory.match_rule(
            source=MatchSource.BODY_JSON,
            operator=MatchOperator.EXISTS,
            expected="any",
            key="token",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(body={"token": "secret"}),
            [rule],
        )

        assert result.matched is True

    @pytest.mark.asyncio
    async def test_body_json_field_absent(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет отсутствие поля в json body."""
        rule = mock_factory.match_rule(
            source=MatchSource.BODY_JSON,
            operator=MatchOperator.EXISTS,
            expected="any",
            key="token",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(body={"other": "value"}),
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
            operator=MatchOperator.EXISTS,
            expected="any",
            key="authorization",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(
                headers={"authorization": "Bearer token"},
            ),
            [rule],
        )

        assert result.score > 0
