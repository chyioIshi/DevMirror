import pytest

from app.domain.mocks import InvalidMatchRuleError
from app.domain.mocks.models import MatchRule
from app.domain.shared import MatchOperator, MatchSource


class TestMatchRule:
    """Проверяет инварианты MatchRule."""

    @pytest.mark.parametrize(
        "source",
        [MatchSource.HEADER, MatchSource.QUERY, MatchSource.BODY_JSON],
    )
    def test_key_is_required_for_key_based_sources(self, source: MatchSource) -> None:
        """Проверяет наличие обязательного поля key
        при создании MatchRule для источников с ключом.
        """
        with pytest.raises(InvalidMatchRuleError):
            MatchRule(source=source, operator=MatchOperator.EQ, expected="value")

    def test_expected_is_required_except_exists_operator(self) -> None:
        """Проверяет наличие обязательного поля expected
        при создании MatchRule для обычных операторов.
        """
        with pytest.raises(InvalidMatchRuleError):
            MatchRule(
                source=MatchSource.PATH,
                operator=MatchOperator.EQ,
            )

    def test_exists_operator_allows_missing_expected(self) -> None:
        """Проверяет, что EXISTS не требует наличие поля expected
        при создании MatchRule.
        """
        rule = MatchRule(
            source=MatchSource.HEADER,
            key="x-test",
            operator=MatchOperator.EXISTS,
        )

        assert rule.expected is None

    def test_in_operator_requires_list_expected(self) -> None:
        """Проверяет, что IN требует список наличие поля expected
        при создании MatchRule.
        """
        with pytest.raises(InvalidMatchRuleError):
            MatchRule(
                source=MatchSource.HEADER,
                key="x-test",
                operator=MatchOperator.IN,
                expected="value",
            )
