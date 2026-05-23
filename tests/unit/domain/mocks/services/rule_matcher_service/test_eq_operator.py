import pytest

from app.domain.shared import MatchOperator, MatchSource


class TestEqOperator:
    """Проверяет оператор EQ."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "header_value,expected,should_match",
        [
            ("user1", "user1", True),
            ("user2", "user1", False),
            ("", "user1", False),
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
        """Проверяет точное совпадение header."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.EQ,
            expected=expected,
            key="user",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers={"user": header_value}),
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
            operator=MatchOperator.EQ,
            expected="user1",
            key="user",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(),
            [rule],
        )

        assert result.matched is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "query_string,expected,should_match",
        [
            ("status=active", "active", True),
            ("status=inactive", "active", False),
        ],
    )
    async def test_query(
        self,
        request_factory,
        matcher,
        mock_factory,
        query_string,
        expected,
        should_match,
    ) -> None:
        """Проверяет точное совпадение query-параметра."""
        rule = mock_factory.match_rule(
            source=MatchSource.QUERY,
            operator=MatchOperator.EQ,
            expected=expected,
            key="status",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(query_string=query_string),
            [rule],
        )

        assert result.matched is should_match

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "body,key,expected,should_match",
        [
            ({"userId": "abc"}, "userId", "abc", True),
            ({"userId": "xyz"}, "userId", "abc", False),
            ({}, "userId", "abc", False),
            (None, "userId", "abc", False),
        ],
    )
    async def test_body_json(
        self,
        request_factory,
        matcher,
        mock_factory,
        body,
        key,
        expected,
        should_match,
    ) -> None:
        """Проверяет точное совпадение поля json body."""
        rule = mock_factory.match_rule(
            source=MatchSource.BODY_JSON,
            operator=MatchOperator.EQ,
            expected=expected,
            key=key,
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(body=body),
            [rule],
        )

        assert result.matched is should_match

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
            operator=MatchOperator.EQ,
            expected="user1",
            key="user",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers={"user": "user1"}),
            [rule],
        )

        assert result.score > 0

    @pytest.mark.asyncio
    async def test_no_match_score_is_zero(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет, что несовпадение дает нулевой score."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.EQ,
            expected="user1",
            key="user",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(headers={"user": "user2"}),
            [rule],
        )

        assert result.score == 0

    @pytest.mark.asyncio
    async def test_path(self, request_factory, matcher, mock_factory) -> None:
        """Проверяет точное совпадение path."""
        rule = mock_factory.match_rule(
            source=MatchSource.PATH,
            operator=MatchOperator.EQ,
            expected="/users",
            key="",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(path="/users"),
            [rule],
        )

        assert result.matched is True
