from collections.abc import Sequence
from typing import Final

from app.domain.mocks.models import Mock
from app.domain.mocks.models.resolution import (
    CandidateEvaluation,
    CandidateRank,
    MockResolutionResult,
    ResolvedMock,
    RuleMatchResult,
)
from app.domain.mocks.policies import MockSelectionPolicy
from app.domain.mocks.services.rule_matcher_service import RuleMatcherService
from app.domain.request_contexts import RequestContext


class MockResolutionService:
    """Резолвит наиболее подходящий мок из доступных кандидатов."""

    def __init__(
        self,
        rule_matcher: RuleMatcherService,
        selection_policy: MockSelectionPolicy,
    ) -> None:
        self._rule_matcher: Final[RuleMatcherService] = rule_matcher
        self._selection_policy: Final[MockSelectionPolicy] = selection_policy

    async def resolve_best(
        self,
        request_context: RequestContext,
        candidates: Sequence[Mock],
        *,
        requested_scope: str,
    ) -> MockResolutionResult:
        """Оценивает кандидатов на соответствие запросу и возвращает наиболее
        подходящий мок.

        Args:
            request_context: Контекст входящего запроса, содержащий метод,
            путь и другие данные запроса.
            candidates: Список кандидатов на мок, которые соответствуют методу,
            пути и scope.
            requested_scope: Scope, для которого выполняется разрешение.

        Returns:
            Результат резолва, включающий запрошенный scope, найденный мок
            (или None, если подходящих кандидатов нет) и подробности оценки всех кандидатов.
        """
        evaluations = await self.evaluate_candidates(
            request_context=request_context,
            candidates=candidates,
            requested_scope=requested_scope,
        )
        resolved_mock = self.select_best_candidate(
            evaluations,
            requested_scope=requested_scope,
        )
        return MockResolutionResult(
            requested_scope=requested_scope,
            resolved_mock=resolved_mock,
            evaluations=evaluations,
        )

    async def evaluate_candidates(
        self,
        request_context: RequestContext,
        candidates: Sequence[Mock],
        *,
        requested_scope: str,
    ) -> list[CandidateEvaluation]:
        """Матчит каждого кандидата с запросом
        и ранжирует подходящие кандидаты по приоритету и прецедентности scope.

        Args:
            request_context: Контекст входящего запроса, содержащий метод,
            путь и другие данные запроса.
            candidates: Список кандидатов на мок, которые соответствуют методу,
            пути и scope.
            requested_scope: Scope, для которого выполняется разрешение.

        Returns:
            Список оценок кандидатов, включающий информацию
            о соответствии каждого кандидата запросу и его ранг
            среди подходящих кандидатов.
        """
        evaluations: list[CandidateEvaluation] = []
        for candidate in candidates:
            evaluations.append(
                await self._evaluate_candidate(
                    request_context=request_context,
                    candidate=candidate,
                    requested_scope=requested_scope,
                ),
            )
        return evaluations

    def select_best_candidate(
        self,
        evaluations: Sequence[CandidateEvaluation],
        *,
        requested_scope: str,
    ) -> ResolvedMock | None:
        """Выбирает наиболее подходящего кандидата путем ранжирования.

        Args:
            evaluations: Список оценок кандидатов, включающий информацию
                о соответствии каждого кандидата запросу и его ранг
                среди подходящих кандидатов.
            requested_scope: Scope, для которого выполняется разрешение.

        Returns:
            Наиболее подходящий мок-кандидат, или None, если подходящих
            кандидатов нет
        """
        matched_candidates = [evaluation for evaluation in evaluations if evaluation.matched]
        if not matched_candidates:
            return None

        best_candidate = max(
            matched_candidates,
            key=lambda evaluation: self._rank_for(evaluation).sort_key(),
        )
        return ResolvedMock(
            mock=best_candidate.mock,
            scope=requested_scope,
            rule_result=best_candidate.rule_result,
        )

    async def _evaluate_candidate(
        self,
        *,
        request_context: RequestContext,
        candidate: Mock,
        requested_scope: str,
    ) -> CandidateEvaluation:
        """Матчит одного кандидата с запросом и определяет его ранг на основании
        метода rank_candidate класса MockSelectionPolicy.

        Args:
            request_context: Контекст входящего запроса, содержащий метод, путь и другие
                данные запроса.
            candidate: Кандидат на мок, который соответствует методу, пути и scope.
            requested_scope: Scope, для которого выполняется разрешение.

        Returns:
            Оценка кандидата (CandidateEvaluation), включающая информацию о соответствии кандидата
            запросу и его ранге среди подходящих кандидатов.
        """
        rule_match_result: RuleMatchResult = await self._rule_matcher.match_rules(
            request_context,
            candidate.match_rules,
        )
        if not rule_match_result.matched:
            return CandidateEvaluation(
                mock=candidate,
                rule_result=rule_match_result,
            )

        return CandidateEvaluation(
            mock=candidate,
            rule_result=rule_match_result,
            rank=self._selection_policy.rank_candidate(
                candidate,
                requested_scope=requested_scope,
                rule_result=rule_match_result,
            ),
        )

    @staticmethod
    def _rank_for(evaluation: CandidateEvaluation) -> CandidateRank:
        """Возвращает ранг кандидата, если он соответствует запросу,
        или выбрасывает исключение, если ранг не определен.

        Args:
            evaluation: Оценка кандидата, включающая информацию о соответствии кандидата
                запросу и его ранге среди подходящих кандидатов.

        Returns:
            Ранг кандидата (CandidateRank), если он соответствует запросу.
        """
        if evaluation.rank is None:
            msg = "Matched candidate evaluation must have a rank."
            raise ValueError(msg)
        return evaluation.rank
