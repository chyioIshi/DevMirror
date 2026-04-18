from typing import Final

from app.application.services.request_log_service import RequestLogService
from app.domain.mocks.models.resolution import CandidateRank, RuleMatchResult
from app.domain.mocks.models.resolution.resolved_mock import ResolvedMock
from app.domain.mocks.policies.selection_policy import MockSelectionPolicy
from app.domain.mocks.repository import MockRepository
from app.domain.mocks.services.rule_matcher import RuleMatcherService
from app.domain.request_contexts.models.request_context import RequestContext
from app.domain.shared.ports.scope_resolver import ScopeResolver


class MockResolverService:
    """Подбирает наиболее подходящий мок для входящего запроса."""

    def __init__(
        self,
        mock_repository: MockRepository,
        request_log_service: RequestLogService,
        scope_resolver: ScopeResolver,
        rule_matcher: RuleMatcherService,
        selection_policy: MockSelectionPolicy,
        *,
        default_scope: str = "global",
    ) -> None:
        self._mock_repository: Final[MockRepository] = mock_repository
        self._request_log_service: Final[RequestLogService] = request_log_service
        self._scope_resolver: Final[ScopeResolver] = scope_resolver
        self._rule_matcher: Final[RuleMatcherService] = rule_matcher
        self._selection_policy: Final[MockSelectionPolicy] = selection_policy
        self._default_scope: Final[str] = default_scope

    async def resolve(self, request_context: RequestContext) -> ResolvedMock | None:
        """Подбирает наиболее подходящий мок и пишет запись в журнал запросов."""
        scope: str = await self._scope_resolver.resolve_scope(request_context)
        candidate_scopes: list[str] = [scope]
        if scope != self._default_scope:
            candidate_scopes.append(self._default_scope)

        candidates = await self._mock_repository.list_candidates(
            method=request_context.method,
            path=request_context.path,
            scopes=candidate_scopes,
        )

        ranked_matches: list[tuple[CandidateRank, ResolvedMock]] = []

        for candidate in candidates:
            rule_match_result: RuleMatchResult = (
                await self._rule_matcher.match_rules(
                    request_context, candidate.match_rules,
                )
            )
            if not rule_match_result.matched:
                continue

            rank: CandidateRank = self._selection_policy.rank_candidate(
                candidate,
                requested_scope=scope,
                rule_result=rule_match_result,
            )
            ranked_matches.append(
                (rank, ResolvedMock(
                    mock=candidate,
                    scope=scope,
                    rule_result=rule_match_result,
                )),
            )

        if not ranked_matches:
            await self._request_log_service.create_record(
                request_context=request_context,
                scope=scope,
                resolved_mock=None,
            )
            return None

        ranked_matches.sort(
            key=lambda item: item[0].sort_key(),
            reverse=True,
        )
        resolved_mock = ranked_matches[0][1]
        await self._request_log_service.create_record(
            request_context=request_context,
            scope=scope,
            resolved_mock=resolved_mock,
        )
        return resolved_mock
