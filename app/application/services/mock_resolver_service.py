import logging
from typing import Final

from app.application.services.request_log_service import RequestLogService
from app.domain.mocks import MockRepository
from app.domain.mocks.models.resolution import MockResolutionResult, ResolvedMock
from app.domain.mocks.services import MockResolutionService
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
        mock_resolution_service: MockResolutionService,
        *,
        default_scope: str = "global",
    ) -> None:
        self._mock_repository: Final[MockRepository] = mock_repository
        self._request_log_service: Final[RequestLogService] = request_log_service
        self._scope_resolver: Final[ScopeResolver] = scope_resolver
        self._mock_resolution_service: Final[MockResolutionService] = (
            mock_resolution_service
        )
        self._default_scope: Final[str] = default_scope

    async def resolve(self, request_context: RequestContext) -> ResolvedMock | None:
        """Оркестратор резолва мока, включающий в себя:
        
        1. получение кандидатов из репозитория,
        2. резолвинг мока,
        3. создание записи в журнале запросов.
        
        Args:
            request_context: Контекст входящего запроса, содержащий метод, путь и другие данные запроса.

        Returns:
            Наиболее подходящий мок-кандидат, или None, если подходящих кандидатов нет.
        """
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
            (
                f"Получено {len(candidates)} кандидатов для запроса "
                f"{request_context.method} {request_context.path} в scope {scope}"
            ),
            extra={
                "method": str(request_context.method),
                "path": request_context.path,
                "scope": scope,
                "candidate_count": len(candidates),
            },
        )

        resolution_result: MockResolutionResult = (
            await self._mock_resolution_service.resolve_best(
                request_context=request_context,
                candidates=candidates,
                requested_scope=scope,
            )
        )

        if resolution_result.resolved_mock is None:
            await self._request_log_service.create_record(
                request_context=request_context,
                scope=scope,
                resolved_mock=None,
            )
            logger.debug(
                (
                    f"Мок не найден для запроса {request_context.method} "
                    f"{request_context.path} в scope {scope}"
                ),
                extra={
                    "method": str(request_context.method),
                    "path": request_context.path,
                    "scope": scope,
                },
            )
            return None

        resolved_mock = resolution_result.resolved_mock
        await self._request_log_service.create_record(
            request_context=request_context,
            scope=scope,
            resolved_mock=resolved_mock,
        )
        logger.debug(
            (
                f"Найден мок {resolved_mock.mock.name} с id={resolved_mock.mock.id} "
                f"для запроса {request_context.method} {request_context.path} "
                f"в scope {scope}"
            ),
            extra={
                "mock_id": resolved_mock.mock.id,
                "method": str(request_context.method),
                "path": request_context.path,
                "scope": scope,
                "matched_count": resolution_result.matched_count,
            },
        )
        return resolved_mock
