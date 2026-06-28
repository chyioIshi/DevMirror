"""RabbitMQ message publish side effect provider."""

from typing import Any, Protocol

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectType,
)
from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError, RabbitMQPublishError
from app.infra.side_effects.connection_config import ConnectionConfig
from app.infra.side_effects.connection_registry import ConnectionRegistry

_DEFAULT_CONTENT_TYPE = "application/json"
_DEFAULT_DELIVERY_MODE = "persistent"
_DELIVERY_MODES = {"persistent", "transient"}


class RabbitMQSideEffectExecutor(Protocol):
    """Protocol implemented by concrete RabbitMQ publish adapters."""

    async def publish(
        self,
        *,
        connection: ConnectionConfig,
        routing_key: str,
        payload: Any,
        headers: dict[str, str] | None = None,
        content_type: str = _DEFAULT_CONTENT_TYPE,
        delivery_mode: str = _DEFAULT_DELIVERY_MODE,
        message_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Publishes a rendered payload to RabbitMQ and returns adapter metadata."""
        ...


class RabbitMQSideEffectProvider:
    """Executes rendered RabbitMQ ``message_publish`` side effects."""

    provider = "rabbitmq"

    def __init__(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_executor: RabbitMQSideEffectExecutor,
    ) -> None:
        """Initializes the provider with connection configs and an executor."""
        self._connection_registry = connection_registry
        self._side_effect_executor = side_effect_executor

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        """Publishes the rendered payload as a RabbitMQ message."""

        _ = context

        self._validate_effect(effect)
        connection = self._get_connection(effect.target)
        routing_key = SideEffectProviderValidation.required_string(
            effect.target,
            "routing_key",
            "target.routing_key",
            subject="RabbitMQ",
        )
        rendered_options = effect.options
        headers = self._headers(rendered_options)
        content_type = self._content_type(rendered_options)
        delivery_mode = self._delivery_mode(rendered_options)
        message_id = SideEffectProviderValidation.optional_string(
            rendered_options,
            "message_id",
            subject="RabbitMQ",
        )
        correlation_id = SideEffectProviderValidation.optional_string(
            rendered_options,
            "correlation_id",
            subject="RabbitMQ",
        )

        try:
            metadata = await self._side_effect_executor.publish(
                connection=connection,
                routing_key=routing_key,
                payload=effect.payload_template,
                headers=headers,
                content_type=content_type,
                delivery_mode=delivery_mode,
                message_id=message_id,
                correlation_id=correlation_id,
            )
        except RabbitMQPublishError as exc:
            return SideEffectExecutionResult(
                provider=self.provider,
                success=False,
                details={
                    "connection": connection.name,
                    "operation": SideEffectType.MESSAGE_PUBLISH.value,
                    "routing_key": routing_key,
                },
                error=str(exc),
            )

        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "operation": SideEffectType.MESSAGE_PUBLISH.value,
                "routing_key": routing_key,
                "content_type": content_type,
                "delivery_mode": delivery_mode,
                "message_id": message_id,
                "correlation_id": correlation_id,
                **metadata,
            },
        )

    def _validate_effect(self, effect: SideEffect) -> None:
        if effect.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "RabbitMQ side effect provider must match rabbitmq",
                details={"provider": effect.provider},
            )

        if effect.type != SideEffectType.MESSAGE_PUBLISH:
            raise InvalidSideEffectProviderConfigError(
                "RabbitMQ provider supports only message_publish side effects",
                details={"type": effect.type.value},
            )

    def _get_connection(self, target: dict[str, Any]) -> ConnectionConfig:
        connection_name = SideEffectProviderValidation.required_string(
            target,
            "connection",
            "target.connection",
            subject="RabbitMQ",
        )
        connection = self._connection_registry.get(connection_name)
        if connection.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "RabbitMQ target.connection must reference a rabbitmq connection",
                details={
                    "field": "target.connection",
                    "connection": connection_name,
                    "provider": connection.provider,
                },
            )
        return connection

    def _headers(self, options: dict[str, Any]) -> dict[str, str] | None:
        headers = SideEffectProviderValidation.string_mapping(
            options.get("headers"),
            "options.headers",
            subject="RabbitMQ",
        )
        return headers or None

    def _content_type(self, options: dict[str, Any]) -> str:
        return (
            SideEffectProviderValidation.optional_string(
                options,
                "content_type",
                subject="RabbitMQ",
            )
            or _DEFAULT_CONTENT_TYPE
        )

    def _delivery_mode(self, options: dict[str, Any]) -> str:
        delivery_mode = (
            SideEffectProviderValidation.optional_string(
                options,
                "delivery_mode",
                subject="RabbitMQ",
            )
            or _DEFAULT_DELIVERY_MODE
        )
        if delivery_mode in _DELIVERY_MODES:
            return delivery_mode
        raise InvalidSideEffectProviderConfigError(
            "RabbitMQ options.delivery_mode must be persistent or transient",
            details={"field": "options.delivery_mode"},
        )
