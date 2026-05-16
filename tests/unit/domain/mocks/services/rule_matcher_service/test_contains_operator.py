import pytest

from app.domain.shared import MatchOperator, MatchSource


class TestContainsOperator:
    """Проверяет оператор CONTAINS."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "header_value,expected,should_match",
        [
            ("chrome v1", "chrome", True),
            ("mozilla v2", "mozilla", True),
            ("", "tor", False),
        ],
    )
    async def test_header_substring(
        self,
        request_factory,
        matcher,
        mock_factory,
        header_value,
        expected,
        should_match,
    ) -> None:
        """Проверяет поиск подстроки в header."""
        rule = mock_factory.match_rule(
            source=MatchSource.HEADER,
            operator=MatchOperator.CONTAINS,
            expected=expected,
            key="user-agent",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(
                headers={"user-agent": header_value},
            ),
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
            operator=MatchOperator.CONTAINS,
            expected="chrome",
            key="user-agent",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(),
            [rule],
        )

        assert result.matched is False

    @pytest.mark.asyncio
    async def test_body_json_list_element(
        self,
        request_factory,
        matcher,
        mock_factory,
    ) -> None:
        """Проверяет поиск элемента в json теле."""
        rule = mock_factory.match_rule(
            source=MatchSource.BODY_JSON,
            operator=MatchOperator.CONTAINS,
            expected="admin",
            key="roles",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(
                body={"roles": ["admin", "viewer"]}
            ),
            [rule],
        )

        assert result.matched is True

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
            operator=MatchOperator.CONTAINS,
            expected="chrome",
            key="user-agent",
        )
        result = await matcher.match_rules(
            request_factory.create_request_context(
                headers={"user-agent": "chrome v1"},

            ),
            [rule],
        )

        assert result.score > 0
