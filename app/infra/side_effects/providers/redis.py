"""Redis side effect provider."""

from typing import Any, Protocol

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectType,
)
from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError, RedisSideEffectError
from app.infra.side_effects.connection_config import ConnectionConfig
from app.infra.side_effects.connection_registry import ConnectionRegistry


class RedisSideEffectExecutor(Protocol):
    """Protocol implemented by concrete Redis command adapters."""

    async def set_value(
        self,
        *,
        connection: ConnectionConfig,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Sets one Redis key to the rendered value."""
        ...

    async def delete_key(
        self,
        *,
        connection: ConnectionConfig,
        key: str,
    ) -> int:
        """Deletes one Redis key and returns deleted key count."""
        ...

    async def publish(
        self,
        *,
        connection: ConnectionConfig,
        channel: str,
        message: Any,
    ) -> int:
        """Publishes a rendered message to a Redis channel."""
        ...


class RedisSideEffectProvider:
    """Executes rendered Redis side effects.

    The dispatcher passes already-rendered payload_template/options. This
    provider treats them as rendered_payload/rendered_options and does not
    perform template rendering itself.
    """

    provider = "redis"

    def __init__(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_executor: RedisSideEffectExecutor,
    ) -> None:
        """Initializes the provider with connection configs and an executor."""
        self._connection_registry = connection_registry
        self._side_effect_executor = side_effect_executor

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        """Executes the rendered Redis side effect command."""

        _ = context

        self._validate_effect(effect)
        connection = self._get_connection(effect.target)

        operation = effect.type.value
        try:
            match effect.type:
                case SideEffectType.REDIS_SET:
                    return await self._execute_set(effect=effect, connection=connection)
                case SideEffectType.REDIS_DELETE:
                    return await self._execute_delete(effect=effect, connection=connection)
                case SideEffectType.REDIS_PUBLISH:
                    return await self._execute_publish(effect=effect, connection=connection)
        except RedisSideEffectError as exc:
            return SideEffectExecutionResult(
                provider=self.provider,
                success=False,
                details={"connection": connection.name, "operation": operation},
                error=str(exc),
            )

        raise InvalidSideEffectProviderConfigError(
            "Redis provider supports only Redis side effect types",
            details={"type": effect.type.value},
        )

    async def _execute_set(
        self,
        *,
        effect: SideEffect,
        connection: ConnectionConfig,
    ) -> SideEffectExecutionResult:
        key = SideEffectProviderValidation.required_string(
            effect.target, "key", "target.key", subject="Redis"
        )
        ttl_seconds = SideEffectProviderValidation.optional_positive_int(
            effect.options,
            "ttl_seconds",
            "options.ttl_seconds",
            subject="Redis",
        )
        rendered_payload = effect.payload_template

        await self._side_effect_executor.set_value(
            connection=connection,
            key=key,
            value=rendered_payload,
            ttl_seconds=ttl_seconds,
        )
        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "operation": SideEffectType.REDIS_SET.value,
                "key": key,
                "ttl_seconds": ttl_seconds,
            },
        )

    async def _execute_delete(
        self,
        *,
        effect: SideEffect,
        connection: ConnectionConfig,
    ) -> SideEffectExecutionResult:
        key = SideEffectProviderValidation.required_string(
            effect.target, "key", "target.key", subject="Redis"
        )

        deleted_count = await self._side_effect_executor.delete_key(
            connection=connection,
            key=key,
        )
        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "operation": SideEffectType.REDIS_DELETE.value,
                "key": key,
                "deleted_count": deleted_count,
            },
        )

    async def _execute_publish(
        self,
        *,
        effect: SideEffect,
        connection: ConnectionConfig,
    ) -> SideEffectExecutionResult:
        channel = SideEffectProviderValidation.required_string(
            effect.target,
            "channel",
            "target.channel",
            subject="Redis",
        )
        rendered_payload = effect.payload_template

        receiver_count = await self._side_effect_executor.publish(
            connection=connection,
            channel=channel,
            message=rendered_payload,
        )
        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "operation": SideEffectType.REDIS_PUBLISH.value,
                "channel": channel,
                "receiver_count": receiver_count,
            },
        )

    def _validate_effect(self, effect: SideEffect) -> None:
        if effect.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Redis side effect provider must match redis",
                details={"provider": effect.provider},
            )

        if effect.type not in {
            SideEffectType.REDIS_SET,
            SideEffectType.REDIS_DELETE,
            SideEffectType.REDIS_PUBLISH,
        }:
            raise InvalidSideEffectProviderConfigError(
                "Redis provider supports only Redis side effect types",
                details={"type": effect.type.value},
            )

    def _get_connection(self, target: dict[str, Any]) -> ConnectionConfig:
        connection_name = SideEffectProviderValidation.required_string(
            target,
            "connection",
            "target.connection",
            subject="Redis",
        )
        connection = self._connection_registry.get(connection_name)
        if connection.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Redis target.connection must reference a redis connection",
                details={
                    "field": "target.connection",
                    "connection": connection_name,
                    "provider": connection.provider,
                },
            )
        return connection
