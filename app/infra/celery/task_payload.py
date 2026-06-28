"""Typed Celery task payload contracts for side effect execution."""

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionStrategy,
    SideEffectFailPolicy,
    SideEffectMode,
    SideEffectType,
)


class SideEffectTaskPayload(BaseModel):
    """Broker payload for one side effect declaration."""

    model_config = ConfigDict(extra="forbid")

    type: SideEffectType
    provider: str
    target: dict[str, Any]
    payload_template: dict[str, Any]
    options: dict[str, Any] = Field(default_factory=dict)
    mode: SideEffectMode = SideEffectMode.ASYNC
    fail_policy: SideEffectFailPolicy = SideEffectFailPolicy.IGNORE
    execution_strategy: SideEffectExecutionStrategy = SideEffectExecutionStrategy.PARALLEL
    enabled: bool = True

    @classmethod
    def from_domain(cls, side_effect: SideEffect) -> Self:
        """Build a task payload from a domain side effect."""
        return cls(
            type=side_effect.type,
            provider=side_effect.provider,
            target=side_effect.target,
            payload_template=side_effect.payload_template,
            options=side_effect.options,
            mode=side_effect.mode,
            fail_policy=side_effect.fail_policy,
            execution_strategy=side_effect.execution_strategy,
            enabled=side_effect.enabled,
        )

    def to_domain(self) -> SideEffect:
        """Restore the domain side effect from this task payload."""
        return SideEffect(
            type=self.type,
            provider=self.provider,
            target=self.target,
            payload_template=self.payload_template,
            options=self.options,
            mode=self.mode,
            fail_policy=self.fail_policy,
            execution_strategy=self.execution_strategy,
            enabled=self.enabled,
        )


class SideEffectContextTaskPayload(BaseModel):
    """Broker payload for side effect execution context."""

    model_config = ConfigDict(extra="forbid")

    request: dict[str, Any] = Field(default_factory=dict)
    mock: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] = Field(default_factory=dict)
    execution: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_domain(cls, context: SideEffectContext) -> Self:
        """Build a task payload from a domain side effect context."""
        return cls(
            request=context.request,
            mock=context.mock,
            response=context.response,
            execution=context.execution,
        )

    def to_domain(self) -> SideEffectContext:
        """Restore the domain context from this task payload."""
        return SideEffectContext(
            request=self.request,
            mock=self.mock,
            response=self.response,
            execution=self.execution,
        )


class DispatchSideEffectTaskPayload(BaseModel):
    """Celery payload for dispatching one side effect."""

    model_config = ConfigDict(extra="forbid")

    side_effect: SideEffectTaskPayload
    context: SideEffectContextTaskPayload

    @classmethod
    def from_domain(
        cls,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> Self:
        """Build the Celery task payload from domain values."""
        return cls(
            side_effect=SideEffectTaskPayload.from_domain(side_effect),
            context=SideEffectContextTaskPayload.from_domain(context),
        )

    def to_side_effect(self) -> SideEffect:
        """Restore the domain side effect from this task payload."""
        return self.side_effect.to_domain()

    def to_context(self) -> SideEffectContext:
        """Restore the domain context from this task payload."""
        return self.context.to_domain()


class DispatchSideEffectsBatchTaskPayload(BaseModel):
    """Celery payload for dispatching an ordered side effect batch."""

    model_config = ConfigDict(extra="forbid")

    side_effects: list[SideEffectTaskPayload]
    context: SideEffectContextTaskPayload

    @classmethod
    def from_domain(
        cls,
        side_effects: list[SideEffect],
        context: SideEffectContext,
    ) -> Self:
        """Build the Celery batch task payload from domain values."""
        return cls(
            side_effects=[
                SideEffectTaskPayload.from_domain(side_effect) for side_effect in side_effects
            ],
            context=SideEffectContextTaskPayload.from_domain(context),
        )

    def to_side_effects(self) -> list[SideEffect]:
        """Restore domain side effects from this batch task payload."""
        return [side_effect.to_domain() for side_effect in self.side_effects]

    def to_context(self) -> SideEffectContext:
        """Restore the domain context from this batch task payload."""
        return self.context.to_domain()
