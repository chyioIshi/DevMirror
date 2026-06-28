"""aio-pika-backed RabbitMQ side effect executor."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import aio_pika

from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError, RabbitMQPublishError
from app.infra.side_effects.connection_config import ConnectionConfig

_EXCHANGE_TYPES = {"direct", "topic", "fanout", "headers"}
_DEFAULT_EXCHANGE_TYPE = "topic"
_DEFAULT_DELIVERY_MODE = "persistent"


@dataclass(slots=True, frozen=True)
class RabbitMQSideEffectExecutorConfig:
    """Validated RabbitMQ executor configuration."""

    connection_name: str
    url: str
    exchange: str
    exchange_type: str
    timeout_seconds: float | None
    declare_exchange: bool
    durable_exchange: bool

    def key(self) -> tuple[str, str, str, str, float | None, bool, bool]:
        """Returns the cache key for a RabbitMQ channel/exchange created from this config."""
        return (
            self.connection_name,
            self.url,
            self.exchange,
            self.exchange_type,
            self.timeout_seconds,
            self.declare_exchange,
            self.durable_exchange,
        )


@dataclass(slots=True)
class RabbitMQPublishResources:
    """Reusable RabbitMQ publish resources."""

    connection: Any
    channel: Any
    exchange: Any


class AsyncRabbitMQSideEffectExecutor:
    """Publishes RabbitMQ messages using reusable aio-pika connections/channels."""

    def __init__(self) -> None:
        """Initializes an empty RabbitMQ resource cache."""
        self._resources: dict[
            tuple[str, str, str, str, float | None, bool, bool],
            RabbitMQPublishResources,
        ] = {}
        self._resource_lock = asyncio.Lock()

    async def publish(
        self,
        *,
        connection: ConnectionConfig,
        routing_key: str,
        payload: Any,
        headers: dict[str, str] | None = None,
        content_type: str = "application/json",
        delivery_mode: str = _DEFAULT_DELIVERY_MODE,
        message_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Publishes a rendered payload to RabbitMQ."""
        config = self._config(connection)
        try:
            message = aio_pika.Message(
                body=self._serialize_payload(payload),
                headers=self._message_headers(headers),
                content_type=content_type,
                delivery_mode=self._delivery_mode(delivery_mode),
                message_id=message_id,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            raise RabbitMQPublishError(
                "RabbitMQ message serialization failed",
                details={"stage": "serialization", "connection": connection.name},
            ) from exc

        resources = await self._publish_resources(config)
        try:
            await resources.exchange.publish(
                message,
                routing_key=routing_key,
                timeout=config.timeout_seconds,
            )
        except Exception as exc:
            raise RabbitMQPublishError(
                "RabbitMQ message publish failed",
                details={
                    "stage": "publish",
                    "connection": connection.name,
                    "exchange": config.exchange,
                    "routing_key": routing_key,
                },
            ) from exc

        return {
            "exchange": config.exchange,
            "exchange_type": config.exchange_type,
            "routing_key": routing_key,
        }

    async def aclose(self) -> None:
        """Closes all cached RabbitMQ channels and connections."""
        async with self._resource_lock:
            resources = list(self._resources.values())
            try:
                results: list[object] = await asyncio.gather(
                    *[
                        close
                        for resource in resources
                        for close in (resource.channel.close(), resource.connection.close())
                    ],
                    return_exceptions=True,
                )
            finally:
                self._resources.clear()

        errors = [str(result) for result in results if isinstance(result, Exception)]
        if errors:
            raise RabbitMQPublishError(
                "RabbitMQ resource close failed",
                details={"stage": "close", "errors": errors},
            )

    async def _publish_resources(
        self,
        config: RabbitMQSideEffectExecutorConfig,
    ) -> RabbitMQPublishResources:
        key = config.key()
        resources = self._resources.get(key)
        if resources is not None:
            return resources

        async with self._resource_lock:
            resources = self._resources.get(key)
            if resources is not None:
                return resources

            try:
                connection = await aio_pika.connect_robust(
                    config.url,
                    timeout=config.timeout_seconds,
                )
                channel = await connection.channel()
                exchange = await self._exchange(channel, config)
            except Exception as exc:
                raise RabbitMQPublishError(
                    "RabbitMQ connection setup failed",
                    details={"stage": "connect", "connection": config.connection_name},
                ) from exc

            resources = RabbitMQPublishResources(
                connection=connection,
                channel=channel,
                exchange=exchange,
            )
            self._resources[key] = resources
            return resources

    async def _exchange(
        self,
        channel: Any,
        config: RabbitMQSideEffectExecutorConfig,
    ) -> Any:
        if not config.exchange:
            return channel.default_exchange
        if config.declare_exchange:
            return await channel.declare_exchange(
                config.exchange,
                type=config.exchange_type,
                durable=config.durable_exchange,
            )
        return await channel.get_exchange(config.exchange, ensure=False)

    def _config(self, connection: ConnectionConfig) -> RabbitMQSideEffectExecutorConfig:
        settings = connection.settings
        exchange = (
            SideEffectProviderValidation.optional_string(
                settings,
                "exchange",
                subject="RabbitMQ",
            )
            or ""
        )
        exchange_type = (
            SideEffectProviderValidation.optional_string(
                settings,
                "exchange_type",
                subject="RabbitMQ",
            )
            or _DEFAULT_EXCHANGE_TYPE
        )
        if exchange_type not in _EXCHANGE_TYPES:
            raise InvalidSideEffectProviderConfigError(
                "RabbitMQ connection.settings.exchange_type must be direct, topic, fanout, or headers",
                details={"field": "connection.settings.exchange_type"},
            )

        return RabbitMQSideEffectExecutorConfig(
            connection_name=connection.name,
            url=SideEffectProviderValidation.required_string(
                settings,
                "url",
                "connection.settings.url",
                subject="RabbitMQ",
            ),
            exchange=exchange,
            exchange_type=exchange_type,
            timeout_seconds=SideEffectProviderValidation.optional_positive_number(
                settings,
                "timeout_seconds",
                "connection.settings.timeout_seconds",
                subject="RabbitMQ",
            ),
            declare_exchange=SideEffectProviderValidation.optional_bool(
                settings,
                "declare_exchange",
                "connection.settings.declare_exchange",
                subject="RabbitMQ",
            )
            or False,
            durable_exchange=self._durable_exchange(settings),
        )

    def _serialize_payload(self, payload: Any) -> bytes:
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, str):
            return payload.encode()
        if payload is None or isinstance(payload, bool | int | float | dict | list):
            return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        raise RabbitMQPublishError(
            "RabbitMQ payload type is not supported",
            details={"stage": "serialization", "payload_type": type(payload).__name__},
        )

    def _delivery_mode(self, delivery_mode: str) -> Any:
        if delivery_mode == "persistent":
            return aio_pika.DeliveryMode.PERSISTENT
        if delivery_mode == "transient":
            return aio_pika.DeliveryMode.NOT_PERSISTENT
        raise RabbitMQPublishError(
            "RabbitMQ delivery mode is not supported",
            details={"stage": "serialization", "delivery_mode": delivery_mode},
        )

    def _message_headers(self, headers: dict[str, str] | None) -> dict[str, Any] | None:
        if headers is None:
            return None
        return dict(headers)

    def _durable_exchange(self, settings: dict[str, Any]) -> bool:
        if settings.get("durable_exchange") is None:
            return True
        return bool(
            SideEffectProviderValidation.optional_bool(
                settings,
                "durable_exchange",
                "connection.settings.durable_exchange",
                subject="RabbitMQ",
            ),
        )
