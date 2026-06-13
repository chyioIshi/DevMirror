"""Kafka message publish side effect provider."""

from typing import Any, Protocol

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectType,
)
from app.infra.exceptions import InvalidSideEffectProviderConfigError
from app.infra.side_effects.connection_config import ConnectionConfig
from app.infra.side_effects.connection_registry import ConnectionRegistry


class KafkaMessageProducer(Protocol):
    """Protocol implemented by concrete Kafka producer adapters.

    Headers are plain string headers at provider boundary. Concrete producer
    adapters convert them to the target Kafka client representation.
    """

    async def publish(
        self,
        *,
        bootstrap_servers: str | list[str],
        topic: str,
        value: Any,
        key: str | None = None,
        headers: dict[str, str] | None = None,
        client_id: str | None = None,
    ) -> None:
        """Publishes a message to Kafka."""
        ...


class KafkaSideEffectProvider:
    """Executes rendered Kafka ``message_publish`` side effects.

    The dispatcher passes already-rendered payload_template/options. This
    provider treats them as rendered_payload/rendered_options and does not
    perform template rendering itself.
    """

    provider = "kafka"

    def __init__(
        self,
        connection_registry: ConnectionRegistry,
        producer: KafkaMessageProducer,
    ) -> None:
        """Initializes the provider with connection configs and a producer adapter."""
        self._connection_registry = connection_registry
        self._producer = producer

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        """Publishes a rendered payload as a Kafka message value."""

        _ = context

        self._validate_effect(effect)

        connection = self._get_connection(effect.target)
        settings = connection.settings
        bootstrap_servers = self._bootstrap_servers(
            settings,
            "bootstrap_servers",
            "connection.settings.bootstrap_servers",
        )
        client_id = self._optional_string(settings, "client_id")
        topic = self._required_string(effect.target, "destination", "target.destination")
        rendered_payload = effect.payload_template
        rendered_options = effect.options
        key = self._optional_key(rendered_options)
        headers = self._headers(rendered_options)

        try:
            await self._producer.publish(
                bootstrap_servers=bootstrap_servers,
                topic=topic,
                value=rendered_payload,
                key=key,
                headers=headers,
                client_id=client_id,
            )
        except Exception as exc:
            return SideEffectExecutionResult(
                provider=self.provider,
                success=False,
                details={"topic": topic, "key": key},
                error=str(exc),
            )

        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "topic": topic,
                "key": key,
                "client_id": client_id,
            },
        )

    def _validate_effect(self, effect: SideEffect) -> None:
        if effect.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Kafka side effect provider must match kafka",
                details={"provider": effect.provider},
            )

        if effect.type != SideEffectType.MESSAGE_PUBLISH:
            raise InvalidSideEffectProviderConfigError(
                "Kafka provider supports only message_publish side effects",
                details={"type": effect.type.value},
            )

    def _get_connection(self, target: dict[str, Any]) -> ConnectionConfig:
        connection_name = self._required_string(target, "connection", "target.connection")
        connection = self._connection_registry.get(connection_name)
        if connection.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Kafka target.connection must reference a kafka connection",
                details={
                    "field": "target.connection",
                    "connection": connection_name,
                    "provider": connection.provider,
                },
            )
        return connection

    def _headers(self, options: dict[str, Any]) -> dict[str, str] | None:
        headers = self._string_mapping(options.get("headers"), "options.headers")
        return headers or None

    def _optional_key(self, options: dict[str, Any]) -> str | None:
        value = options.get("key")
        if value is None:
            return None
        if isinstance(value, bool | int | float | str):
            return str(value)
        raise InvalidSideEffectProviderConfigError(
            "Kafka options.key must be a string, number, or boolean",
            details={"field": "options.key"},
        )

    def _optional_string(self, mapping: dict[str, Any], key: str) -> str | None:
        value = mapping.get(key)
        if value is None:
            return None
        if isinstance(value, str) and value.strip():
            return value
        raise InvalidSideEffectProviderConfigError(
            f"Kafka {key} must be a non-empty string",
            details={"field": key},
        )

    def _bootstrap_servers(
        self,
        mapping: dict[str, Any],
        key: str,
        field: str,
    ) -> str | list[str]:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list) and value:
            servers = []
            for server in value:
                if not isinstance(server, str) or not server.strip():
                    raise InvalidSideEffectProviderConfigError(
                        f"Kafka {field} must be a non-empty string or list of non-empty strings",
                        details={"field": field},
                    )
                servers.append(server)
            return servers
        raise InvalidSideEffectProviderConfigError(
            f"Kafka {field} must be a non-empty string or list of non-empty strings",
            details={"field": field},
        )

    def _required_string(self, mapping: dict[str, Any], key: str, field: str) -> str:
        value = self._optional_string(mapping, key)
        if value is None:
            raise InvalidSideEffectProviderConfigError(
                f"Kafka {field} must be configured",
                details={"field": field},
            )
        return value

    def _string_mapping(self, value: Any, field: str) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise InvalidSideEffectProviderConfigError(
                f"Kafka {field} must be a dictionary",
                details={"field": field},
            )

        result: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, str):
                raise InvalidSideEffectProviderConfigError(
                    f"Kafka {field} must contain only string values",
                    details={"field": field},
                )
            result[key] = item
        return result
