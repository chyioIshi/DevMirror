
from typing import Final

from fastapi import Request

from app.application.services.mock_selection_policy_service import MockSelectionPolicyService
from app.domain.models.mocks.resolution.candidate_rank import CandidateRank
from app.application.services.request_log_service import RequestLogService
from app.domain.models.mocks.resolution.resolved_mock import ResolvedMock
from app.domain.repositories.mock_repository import MockRepository
from app.application.services.rule_matcher_service import RuleMatcherService
from app.domain.models.mocks.resolution.rule_match_result import RuleMatchResult
from app.domain.services.scope_resolver import ScopeResolver
from app.infra.context.request_context_resolver import RequestContextResolver


class MockResolverService:
    """Подбирает наиболее подходящий мок для входящего запроса."""

    def __init__(
        self,
        mock_repository: MockRepository,
        request_log_service: RequestLogService,
        request_context_resolver: RequestContextResolver,
        scope_resolver: ScopeResolver,
        rule_matcher: RuleMatcherService,
        selection_policy: MockSelectionPolicyService,
        *,
        default_scope: str = "global",
    ) -> None:
        self._mock_repository: Final[MockRepository] = mock_repository
        self._request_log_service: Final[RequestLogService] = request_log_service
        self._request_context_resolver: Final[
            RequestContextResolver
        ] = request_context_resolver
        self._scope_resolver: Final[ScopeResolver] = scope_resolver
        self._rule_matcher: Final[RuleMatcherService] = rule_matcher
        self._selection_policy: Final[MockSelectionPolicyService] = selection_policy
        self._default_scope: Final[str] = default_scope

    async def resolve(self, request: Request) -> ResolvedMock | None:
        """Подбирает наиболее подходящий мок и пишет запись в журнал запросов."""
        request_context = await self._request_context_resolver.resolve(request)
        scope: str = await self._scope_resolver.resolve_scope(request)
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
            key=lambda item: self._selection_policy.sort_key(item[0]),
            reverse=True,
        )
        resolved_mock = ranked_matches[0][1]
        await self._request_log_service.create_record(
            request_context=request_context,
            scope=scope,
            resolved_mock=resolved_mock,
        )
        return resolved_mock
