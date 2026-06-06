"""Application service for dispatching side effects."""

import logging
from collections.abc import Iterable
from dataclasses import replace

from app.application.exceptions import SideEffectExecutionFailedError
from app.application.side_effects.registry import SideEffectProviderRegistry
from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectFailPolicy,
)
from app.domain.mocks.ports import SideEffectProvider
from app.domain.mocks.services import SideEffectTemplateRenderer

logger = logging.getLogger(__name__)


class SideEffectDispatcherService:
    """Coordinates side effect rendering, provider lookup, and failure policy handling."""

    def __init__(
        self,
        registry: SideEffectProviderRegistry,
        renderer: SideEffectTemplateRenderer | None = None,
    ) -> None:
        """Initializes the side effect dispatcher service."""
        self._registry = registry
        self._renderer = renderer or SideEffectTemplateRenderer()

    async def dispatch(
        self,
        side_effects: Iterable[SideEffect],
        context: SideEffectContext,
    ) -> list[SideEffectExecutionResult]:
        """Executes enabled side effects and returns provider execution results."""
        results: list[SideEffectExecutionResult] = []

        for side_effect in side_effects:
            if not side_effect.enabled:
                continue

            provider = self._registry.get(side_effect.provider)
            rendered_effect = self._render_effect(side_effect, context)
            result = await self._execute_with_policy(provider, rendered_effect, context)
            if result is not None:
                results.append(result)

        return results

    def _render_effect(
        self,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffect:
        return replace(
            side_effect,
            payload_template=self._renderer.render_payload(side_effect, context),
            options=self._renderer.render_options(side_effect, context),
        )

    async def _execute_with_policy(
        self,
        provider: SideEffectProvider,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult | None:
        if side_effect.fail_policy == SideEffectFailPolicy.IGNORE:
            return await self._execute_ignoring_failures(provider, side_effect, context)

        if side_effect.fail_policy == SideEffectFailPolicy.FAIL_MOCK:
            return await self._execute_or_raise(provider, side_effect, context)

        if side_effect.fail_policy == SideEffectFailPolicy.RETRY:
            return await self._execute_with_retry(provider, side_effect, context)

        raise AssertionError(f"Unsupported side effect fail_policy: {side_effect.fail_policy}")

    async def _execute_ignoring_failures(
        self,
        provider: SideEffectProvider,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        try:
            result = await provider.execute(side_effect, context)
        except Exception as exc:
            logger.exception(
                "Side effect execution failed and was ignored",
                extra={"provider": provider.provider, "fail_policy": side_effect.fail_policy},
            )
            return SideEffectExecutionResult(
                provider=provider.provider,
                success=False,
                error=str(exc),
            )

        if not result.success:
            logger.error(
                "Side effect provider returned a failed result and it was ignored",
                extra={"provider": provider.provider, "details": result.details},
            )
        return result

    async def _execute_or_raise(
        self,
        provider: SideEffectProvider,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        try:
            result = await provider.execute(side_effect, context)
        except Exception as exc:
            raise SideEffectExecutionFailedError(
                provider=provider.provider,
                attempts=1,
                details={"error": str(exc)},
            ) from exc

        if result.success:
            return result

        raise SideEffectExecutionFailedError(
            provider=provider.provider,
            attempts=1,
            details={"error": result.error, "details": result.details},
        )

    async def _execute_with_retry(
        self,
        provider: SideEffectProvider,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        max_attempts = side_effect.options["max_attempts"]
        last_result: SideEffectExecutionResult | None = None
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
                result = await provider.execute(side_effect, context)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Side effect execution attempt failed",
                    extra={
                        "provider": provider.provider,
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                    },
                )
                continue

            last_result = result
            if result.success:
                return result

            logger.warning(
                "Side effect provider returned a failed result",
                extra={
                    "provider": provider.provider,
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "details": result.details,
                },
            )

        details = {
            "error": str(last_error) if last_error is not None else last_result.error,
            "details": last_result.details if last_result is not None else {},
        }
        raise SideEffectExecutionFailedError(
            provider=provider.provider,
            attempts=max_attempts,
            details=details,
        )
