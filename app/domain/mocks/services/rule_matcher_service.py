from collections.abc import Callable
from typing import Any

from app.domain.mocks.models import MatchRule
from app.domain.mocks.models.resolution import (
    RuleEvaluation,
    RuleMatchResult,
)
from app.domain.request_contexts import RequestContext
from app.domain.shared import MatchOperator, MatchSource

OperatorHandler = Callable[[Any, Any], bool]
ValueExtractor = Callable[[RequestContext, MatchRule], Any | None]


class RuleMatcherService:
    """Сопоставляет данные контекста запроса с массивом match rules мока."""

    _SOURCE_SCORE: dict[MatchSource, int] = {
        MatchSource.HEADER: 30,
        MatchSource.BODY_JSON: 25,
        MatchSource.QUERY: 20,
        MatchSource.PATH: 10,
    }
    _OPERATOR_SCORE: dict[MatchOperator, int] = {
        MatchOperator.EQ: 10,
        MatchOperator.NEQ: 8,
        MatchOperator.IN: 7,
        MatchOperator.CONTAINS: 6,
        MatchOperator.EXISTS: 4,
    }

    def __init__(self) -> None:
        """Инициализирует мапу операторов и экстракторов."""
        self._operator_handlers: dict[MatchOperator, OperatorHandler] = {
            MatchOperator.EQ: self._eq,
            MatchOperator.NEQ: self._neq,
            MatchOperator.CONTAINS: self._contains,
            MatchOperator.IN: self._in,
            MatchOperator.EXISTS: self._exists,
        }
        self._value_extractors: dict[MatchSource, ValueExtractor] = {
            MatchSource.HEADER: self._extract_header_value,
            MatchSource.QUERY: self._extract_query_value,
            MatchSource.PATH: self._extract_path_value,
            MatchSource.BODY_JSON: self._extract_body_json_value,
        }

    async def match_rules(
        self,
        request_context: RequestContext,
        match_rules: list[MatchRule],
    ) -> RuleMatchResult:
        """Проверяет все правила и останавливается на первом несовпадении."""
        if not match_rules:
            return RuleMatchResult(matched=True, score=0, evaluations=[])

        evaluations: list[RuleEvaluation] = []
        total_score = 0

        for match_rule in match_rules:
            actual = self._extract_actual_value(request_context, match_rule)
            matched = self._operator_handlers[match_rule.operator](
                actual,
                match_rule.expected,
            )
            score = self._calculate_rule_score(match_rule) if matched else 0
            evaluations.append(
                RuleEvaluation(
                    rule=match_rule,
                    matched=matched,
                    score=score,
                    actual=actual,
                ),
            )

            if not matched:
                return RuleMatchResult(
                    matched=False,
                    score=0,
                    evaluations=evaluations,
                )

            total_score += score

        return RuleMatchResult(
            matched=True,
            score=total_score,
            evaluations=evaluations,
        )

    def _extract_actual_value(
        self,
        request_context: RequestContext,
        rule: MatchRule,
    ) -> Any | None:
        """Извлекает из контекста запроса фактическое значение для правила."""
        extractor = self._value_extractors[rule.source]
        return extractor(request_context, rule)

    def _calculate_rule_score(self, rule: MatchRule) -> int:
        """Вычисляет вклад matched rule в итоговый score."""
        return self._SOURCE_SCORE[rule.source] + self._OPERATOR_SCORE[rule.operator]

    @staticmethod
    def _extract_header_value(
        request_context: RequestContext,
        rule: MatchRule,
    ) -> Any | None:
        """Извлекает значение заголовка по ключу из контекста запроса."""
        return request_context.headers.get(rule.key)

    @staticmethod
    def _extract_query_value(
        request_context: RequestContext,
        rule: MatchRule,
    ) -> Any | None:
        """Извлекает query-значение для ключа правила из контекста запроса."""
        return request_context.query_params.get(rule.key)

    @staticmethod
    def _extract_path_value(
        request_context: RequestContext,
        rule: MatchRule,  # noqa: ARG004
    ) -> Any | None:
        """Возвращает путь запроса из контекста."""
        return request_context.path

    @staticmethod
    def _extract_body_json_value(
        request_context: RequestContext,
        rule: MatchRule,
    ) -> Any | None:
        """Извлекает значение поля из JSON-тела запроса."""
        if isinstance(request_context.body, dict):
            return request_context.body.get(rule.key)
        return None

    @staticmethod
    def _eq(actual: Any, expected: Any) -> bool:
        """Проверяет равенство фактического и ожидаемого значений."""
        return actual == expected

    @staticmethod
    def _neq(actual: Any, expected: Any) -> bool:
        """Проверяет, что существующее значение отличается от ожидаемого."""
        return actual is not None and actual != expected

    @staticmethod
    def _contains(actual: Any, expected: Any) -> bool:
        """Проверяет, содержит ли фактическое значение ожидаемое."""
        if actual is None:
            return False
        if isinstance(actual, list | tuple | set):
            return expected in actual
        if isinstance(actual, dict):
            return expected in actual
        return str(expected) in str(actual)

    @staticmethod
    def _in(actual: Any, expected: Any) -> bool:
        """Проверяет, входит ли фактическое значение в ожидаемый список."""
        if not isinstance(expected, list):
            return False
        if isinstance(actual, list):
            return any(item in expected for item in actual)
        return actual in expected

    @staticmethod
    def _exists(actual: Any, _: Any) -> bool:
        """Проверяет наличие запрошенного значения."""
        return actual is not None
