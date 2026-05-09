import logging
from typing import Final

from app.application.services.request_log_service import RequestLogService
from app.domain.mocks import MockRepository
from app.domain.mocks.models.resolution import CandidateRank, ResolvedMock, RuleMatchResult
from app.domain.mocks.policies import MockSelectionPolicy
from app.domain.mocks.services import RuleMatcherService
from app.domain.request_contexts import RequestContext
from app.domain.shared.ports import ScopeResolver

logger = logging.getLogger(__name__)


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
        logger.debug(
            f"Получено {len(candidates)} кандидатов для запроса {request_context.method} {request_context.path} в scope {scope}",
            extra={
                "method": str(request_context.method),
                "path": request_context.path,
                "scope": scope,
                "candidate_count": len(candidates),
            },
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
            logger.debug(
                f"Мок не найден для запроса {request_context.method} {request_context.path} в scope {scope}",
                extra={
                    "method": str(request_context.method),
                    "path": request_context.path,
                    "scope": scope,
                },
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
        logger.debug(
            f"Найден мок {resolved_mock.mock.name} с id={resolved_mock.mock.id} для запроса {request_context.method} {request_context.path} в scope {scope}",
            extra={
                "mock_id": resolved_mock.mock.id,
                "method": str(request_context.method),
                "path": request_context.path,
                "scope": scope,
                "matched_count": len(ranked_matches),
            },
        )
        return resolved_mock
