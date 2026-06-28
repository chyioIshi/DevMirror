from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.domain.mocks.models import Mock, MockResponse, SideEffect
from app.domain.request_contexts import RequestContext


@dataclass(slots=True)
class SideEffectExecutionCall:
    """Recorded fake side effect execution service call."""

    side_effects: list[SideEffect]
    request: RequestContext
    mock: Mock
    response: MockResponse
    execution: dict[str, Any] | None


@dataclass(slots=True)
class FakeSideEffectExecutionService:
    """Fake SideEffectExecutionService for API integration tests."""

    execute_calls: list[SideEffectExecutionCall] = field(default_factory=list)

    async def execute(
        self,
        *,
        side_effects: Sequence[SideEffect],
        request: RequestContext,
        mock: Mock,
        response: MockResponse,
        execution: dict[str, Any] | None = None,
    ) -> None:
        self.execute_calls.append(
            SideEffectExecutionCall(
                side_effects=list(side_effects),
                request=request,
                mock=mock,
                response=response,
                execution=execution,
            )
        )
