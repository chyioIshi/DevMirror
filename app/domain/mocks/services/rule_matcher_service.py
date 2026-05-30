"""Domain service for matching mock rules against a request context."""

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
    """Matches request context data against a mock's match rules."""

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
        """Initializes operator handlers and value extractors."""
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
        """Checks all rules and stops at the first mismatch.

        Args:
            request_context: Incoming request context.
            match_rules: Matching rules to evaluate.

        Returns:
            Overall rule matching result.
        """
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
        """Extracts the actual value for a rule from the request context.

        Args:
            request_context: Incoming request context.
            rule: Rule whose actual value should be extracted.

        Returns:
            Extracted value or ``None``.
        """
        extractor = self._value_extractors[rule.source]
        return extractor(request_context, rule)

    def _calculate_rule_score(self, rule: MatchRule) -> int:
        """Calculates the score contribution for a matched rule.

        Args:
            rule: Matched rule.

        Returns:
            Rule score contribution.
        """
        return self._SOURCE_SCORE[rule.source] + self._OPERATOR_SCORE[rule.operator]

    @staticmethod
    def _extract_header_value(
        request_context: RequestContext,
        rule: MatchRule,
    ) -> Any | None:
        """Extracts a header value by rule key from the request context.

        Args:
            request_context: Incoming request context.
            rule: Rule that provides the header key.

        Returns:
            Header value or ``None``.
        """
        return request_context.headers.get(rule.key)

    @staticmethod
    def _extract_query_value(
        request_context: RequestContext,
        rule: MatchRule,
    ) -> Any | None:
        """Extracts a query value by rule key from the request context.

        Args:
            request_context: Incoming request context.
            rule: Rule that provides the query key.

        Returns:
            Query value or ``None``.
        """
        return request_context.query_params.get(rule.key)

    @staticmethod
    def _extract_path_value(
        request_context: RequestContext,
        rule: MatchRule,  # noqa: ARG004
    ) -> Any | None:
        """Returns the request path from the context.

        Args:
            request_context: Incoming request context.
            rule: Unused rule argument required by the extractor signature.

        Returns:
            Request path.
        """
        return request_context.path

    @staticmethod
    def _extract_body_json_value(
        request_context: RequestContext,
        rule: MatchRule,
    ) -> Any | None:
        """Extracts a field value from the JSON request body.

        Args:
            request_context: Incoming request context.
            rule: Rule that provides the JSON field key.

        Returns:
            JSON field value or ``None``.
        """
        if isinstance(request_context.body, dict):
            return request_context.body.get(rule.key)
        return None

    @staticmethod
    def _eq(actual: Any, expected: Any) -> bool:
        """Checks equality between actual and expected values.

        Args:
            actual: Actual request value.
            expected: Expected rule value.

        Returns:
            True when values are equal; otherwise False.
        """
        return actual == expected

    @staticmethod
    def _neq(actual: Any, expected: Any) -> bool:
        """Checks that an existing actual value differs from expected.

        Args:
            actual: Actual request value.
            expected: Expected rule value.

        Returns:
            True when actual exists and differs from expected; otherwise False.
        """
        return actual is not None and actual != expected

    @staticmethod
    def _contains(actual: Any, expected: Any) -> bool:
        """Checks whether the actual value contains the expected value.

        Args:
            actual: Actual request value.
            expected: Expected contained value.

        Returns:
            True when actual contains expected; otherwise False.
        """
        if actual is None:
            return False
        if isinstance(actual, list | tuple | set):
            return expected in actual
        if isinstance(actual, dict):
            return expected in actual
        return str(expected) in str(actual)

    @staticmethod
    def _in(actual: Any, expected: Any) -> bool:
        """Checks whether the actual value belongs to the expected list.

        Args:
            actual: Actual request value.
            expected: Expected list of values.

        Returns:
            True when actual is included in expected; otherwise False.
        """
        if not isinstance(expected, list):
            return False
        if isinstance(actual, list):
            return any(item in expected for item in actual)
        return actual in expected

    @staticmethod
    def _exists(actual: Any, _: Any) -> bool:
        """Checks that the requested value exists.

        Args:
            actual: Actual request value.
            _: Unused expected value.

        Returns:
            True when actual is not ``None``; otherwise False.
        """
        return actual is not None
