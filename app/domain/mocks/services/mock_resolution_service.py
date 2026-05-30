"""Domain service for choosing the best mock for a request."""

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
    """Resolves the best matching mock from available candidates."""

    def __init__(
        self,
        rule_matcher: RuleMatcherService,
        selection_policy: MockSelectionPolicy,
    ) -> None:
        """Initializes the service with mock resolution dependencies.

        Args:
            rule_matcher: Service that matches mock rules against a request.
            selection_policy: Policy used to rank matching candidates.
        """
        self._rule_matcher: Final[RuleMatcherService] = rule_matcher
        self._selection_policy: Final[MockSelectionPolicy] = selection_policy

    async def resolve_best(
        self,
        request_context: RequestContext,
        candidates: Sequence[Mock],
        *,
        requested_scope: str,
    ) -> MockResolutionResult:
        """Evaluates candidates against a request and returns the best matching mock.

        Args:
            request_context: Incoming request context with method, path, and request data.
            candidates: Mock candidates matching method, path, and scope prefilters.
            requested_scope: Scope requested for resolution.

        Returns:
            Resolution result containing the requested scope, selected mock, and
            evaluation details for all candidates.
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
        """Matches each candidate against the request and ranks matching candidates.

        Args:
            request_context: Incoming request context with method, path, and request data.
            candidates: Mock candidates matching method, path, and scope prefilters.
            requested_scope: Scope requested for resolution.

        Returns:
            Candidate evaluations with match results and ranks for matching candidates.
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
        """Selects the best matching candidate by rank.

        Args:
            evaluations: Candidate evaluations with match results and optional ranks.
            requested_scope: Scope requested for resolution.

        Returns:
            Resolved mock when a matching candidate exists; otherwise ``None``.
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
        """Matches one candidate against a request and computes its rank.

        Args:
            request_context: Incoming request context with method, path, and request data.
            candidate: Mock candidate matching method, path, and scope prefilters.
            requested_scope: Scope requested for resolution.

        Returns:
            Candidate evaluation with match result and optional rank.
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
        """Returns the rank for a matched candidate evaluation.

        Args:
            evaluation: Candidate evaluation that must contain a rank.

        Returns:
            Candidate rank.

        Raises:
            ValueError: If the matched candidate evaluation has no rank.
        """
        if evaluation.rank is None:
            msg = "Matched candidate evaluation must have a rank."
            raise ValueError(msg)
        return evaluation.rank
