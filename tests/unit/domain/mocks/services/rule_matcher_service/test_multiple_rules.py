import pytest

from app.domain.mocks.models import MatchRule
from app.domain.shared import MatchOperator, MatchSource


@pytest.fixture
def header_and_query_rules() -> list[MatchRule]:
    return [
        MatchRule(
            source=MatchSource.HEADER,
            key="user",
            operator=MatchOperator.EQ,
            expected="user1",
        ),
        MatchRule(
            source=MatchSource.QUERY,
            key="page",
            operator=MatchOperator.EQ,
            expected="2",
        ),
    ]


class TestMultipleRules:
    """Проверяет матчинг нескольких правил."""

    @pytest.mark.asyncio
    async def test_all_rules_match_accumulates_score(
        self,
        request_factory,
        matcher,
        header_and_query_rules,
    ) -> None:
        """Проверяет, что совпавшие правила накапливают score."""
        request_context = request_factory.create_request_context(
            headers={"user": "user1"},
            query_string="page=2",
        )
        result = await matcher.match_rules(request_context, header_and_query_rules)

        assert result.matched is True
        assert len(result.evaluations) == 2
        assert result.score == sum(e.score for e in result.evaluations)

    @pytest.mark.asyncio
    async def test_first_rule_fails_stops_evaluation(
        self,
        request_factory,
        matcher,
        header_and_query_rules,
    ) -> None:
        """Проверяет, что первое несовпадение останавливает вычисление."""
        request_context = request_factory.create_request_context(
            headers={"user": "user2"},
            query_string="page=2",
        )
        result = await matcher.match_rules(request_context, header_and_query_rules)

        assert result.matched is False
        assert result.score == 0
        assert len(result.evaluations) == 1

    @pytest.mark.asyncio
    async def test_second_rule_fails_returns_no_match(
        self,
        request_factory,
        matcher,
        header_and_query_rules,
    ) -> None:
        """Проверяет, что провал второго правила возвращает no match."""
        request_context = request_factory.create_request_context(
            headers={"user": "user1"},
            query_string="page=99",
        )
        result = await matcher.match_rules(request_context, header_and_query_rules)

        assert result.matched is False
        assert result.score == 0

    @pytest.mark.asyncio
    async def test_empty_rules_always_match(self, request_factory, matcher) -> None:
        """Проверяет, что пустой набор правил всегда совпадает."""
        result = await matcher.match_rules(
            request_factory.create_request_context(),
            [],
        )

        assert result.matched is True
        assert result.score == 0
        assert result.evaluations == []

    @pytest.mark.asyncio
    async def test_more_rules_yield_higher_score(self, request_factory, matcher) -> None:
        """Проверяет, что больше совпавших правил дает больший score."""
        one_rule = [
            MatchRule(
                source=MatchSource.HEADER,
                key="user",
                operator=MatchOperator.EQ,
                expected="user1",
            ),
        ]
        two_rules = [
            MatchRule(
                source=MatchSource.HEADER,
                key="user",
                operator=MatchOperator.EQ,
                expected="user1",
            ),
            MatchRule(
                source=MatchSource.QUERY,
                key="page",
                operator=MatchOperator.EQ,
                expected="1",
            ),
        ]
        request_context = request_factory.create_request_context(
            headers={"user": "user1"},
            query_string="page=1",
        )

        score_one = (await matcher.match_rules(request_context, one_rule)).score
        score_two = (await matcher.match_rules(request_context, two_rules)).score

        assert score_two > score_one
