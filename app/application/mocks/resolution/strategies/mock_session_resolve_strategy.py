"""Session-based mock resolver strategy."""

import logging
from typing import Final

from app.application.request_logs import RequestLogService
from app.domain.mocks import MockRepository
from app.domain.mocks.models.resolution import ResolvedMock, RuleMatchResult
from app.domain.request_contexts import RequestContext

logger = logging.getLogger(__name__)


class MockSessionResolveStrategy:
    """Resolves session-scoped mocks before regular matcher evaluation."""

    _SESSION_HEADER_NAME: Final[str] = "mock-session-id"

    def __init__(
        self,
        mock_repository: MockRepository,
        request_log_service: RequestLogService,
    ) -> None:
        """Initializes the session-based resolver strategy."""
        self._mock_repository: Final[MockRepository] = mock_repository
        self._request_log_service: Final[RequestLogService] = request_log_service

    async def resolve(self, request_context: RequestContext) -> ResolvedMock | None:
        """Resolves an active mock by route and ``mock-session-id`` header."""
        session_id = self._session_id_from(request_context)
        if session_id is None:
            return None

        mock = await self._mock_repository.find_latest_by_session_id(
            method=request_context.method,
            path=request_context.path,
            session_id=session_id,
        )
        if mock is None:
            return None

        resolved_mock = ResolvedMock(
            mock=mock,
            scope=mock.scope,
            rule_result=RuleMatchResult(matched=True, score=0),
        )
        await self._request_log_service.create_record(
            request_context=request_context,
            scope=mock.scope,
            resolved_mock=resolved_mock,
        )
        logger.debug(
            "Resolved mock by session",
            extra={
                "mock_id": mock.id,
                "method": str(request_context.method),
                "path": request_context.path,
                "scope": mock.scope,
                "mock_session_id": session_id,
            },
        )
        return resolved_mock

    def _session_id_from(self, request_context: RequestContext) -> str | None:
        for header_name, header_value in request_context.headers.items():
            if header_name.lower() != self._SESSION_HEADER_NAME:
                continue
            session_id = header_value.strip()
            return session_id or None
        return None
