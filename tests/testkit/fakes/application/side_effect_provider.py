from dataclasses import dataclass, field

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectExecutionResult


@dataclass(slots=True)
class FakeSideEffectProvider:
    """Fake side effect provider used by application tests."""

    provider: str = "fake"
    executions: list[tuple[SideEffect, SideEffectContext]] = field(default_factory=list)
    results: list[SideEffectExecutionResult] = field(default_factory=list)
    errors: list[Exception] = field(default_factory=list)

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        self.executions.append((effect, context))

        if self.errors:
            raise self.errors.pop(0)

        if self.results:
            return self.results.pop(0)

        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={"executions": len(self.executions)},
        )
