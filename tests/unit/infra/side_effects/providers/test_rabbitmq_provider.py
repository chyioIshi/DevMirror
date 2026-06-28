from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.exceptions import (
    ConnectionNotFoundError,
    InvalidSideEffectProviderConfigError,
    RabbitMQPublishError,
)
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry
from app.infra.side_effects.providers import RabbitMQSideEffectProvider


@dataclass(slots=True)
class PublishedRabbitMQMessage:
    connection: ConnectionConfig
    routing_key: str
    payload: Any
    headers: dict[str, str] | None
    content_type: str
    delivery_mode: str
    message_id: str | None
    correlation_id: str | None


@dataclass(slots=True)
class FakeRabbitMQSideEffectExecutor:
    published_messages: list[PublishedRabbitMQMessage] = field(default_factory=list)
    error: RabbitMQPublishError | None = None

    async def publish(
        self,
        *,
        connection: ConnectionConfig,
        routing_key: str,
        payload: Any,
        headers: dict[str, str] | None = None,
        content_type: str = "application/json",
        delivery_mode: str = "persistent",
        message_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        if self.error is not None:
            raise self.error

        self.published_messages.append(
            PublishedRabbitMQMessage(
                connection=connection,
                routing_key=routing_key,
                payload=payload,
                headers=headers,
                content_type=content_type,
                delivery_mode=delivery_mode,
                message_id=message_id,
                correlation_id=correlation_id,
            )
        )
        return {"exchange": "mock.events", "exchange_type": "topic"}


class TestRabbitMQSideEffectProvider:
    async def test_publishes_rendered_payload_to_routing_key(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        executor = FakeRabbitMQSideEffectExecutor()
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "main-rabbitmq", "routing_key": "mock.served"},
            payload_template={"event": "mock_served"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=executor,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details == {
            "connection": "main-rabbitmq",
            "operation": "message_publish",
            "routing_key": "mock.served",
            "content_type": "application/json",
            "delivery_mode": "persistent",
            "message_id": None,
            "correlation_id": None,
            "exchange": "mock.events",
            "exchange_type": "topic",
        }
        assert executor.published_messages == [
            PublishedRabbitMQMessage(
                connection=rabbitmq_connection_registry.get("main-rabbitmq"),
                routing_key="mock.served",
                payload={"event": "mock_served"},
                headers=None,
                content_type="application/json",
                delivery_mode="persistent",
                message_id=None,
                correlation_id=None,
            )
        ]

    async def test_passes_headers_message_id_and_correlation_id(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        executor = FakeRabbitMQSideEffectExecutor()
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "main-rabbitmq", "routing_key": "mock.served"},
            options={
                "headers": {"source": "devmirror"},
                "content_type": "application/vnd.devmirror.event+json",
                "delivery_mode": "transient",
                "message_id": "message-1",
                "correlation_id": "correlation-1",
            },
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=executor,
        )

        await provider.execute(effect, side_effect_context)

        published = executor.published_messages[0]
        assert published.headers == {"source": "devmirror"}
        assert published.content_type == "application/vnd.devmirror.event+json"
        assert published.delivery_mode == "transient"
        assert published.message_id == "message-1"
        assert published.correlation_id == "correlation-1"

    async def test_rejects_wrong_provider(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "main-rabbitmq", "routing_key": "mock.served"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must match rabbitmq",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_wrong_side_effect_type(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="rabbitmq",
            target={"connection": "main-rabbitmq", "routing_key": "mock.served"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="supports only message_publish",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_connection(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"routing_key": "mock.served"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.connection must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_unknown_connection(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "missing", "routing_key": "mock.served"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(ConnectionNotFoundError):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_mismatched_connection_provider(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="main-kafka",
                    provider="kafka",
                    settings={"bootstrap_servers": "localhost:9092"},
                )
            ]
        )
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "main-kafka", "routing_key": "mock.served"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must reference a rabbitmq connection",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_routing_key(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "main-rabbitmq", "destination": "mock.events"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.routing_key must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_invalid_headers(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "main-rabbitmq", "routing_key": "mock.served"},
            options={"headers": {"source": 1}},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="options.headers must contain only string values",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_invalid_delivery_mode(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "main-rabbitmq", "routing_key": "mock.served"},
            options={"delivery_mode": "invalid"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="options.delivery_mode must be persistent or transient",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_publish_error_returns_failed_execution_result(
        self,
        rabbitmq_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"connection": "main-rabbitmq", "routing_key": "mock.served"},
        )
        provider = RabbitMQSideEffectProvider(
            connection_registry=rabbitmq_connection_registry,
            side_effect_executor=FakeRabbitMQSideEffectExecutor(
                error=RabbitMQPublishError("publish failed")
            ),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is False
        assert result.details == {
            "connection": "main-rabbitmq",
            "operation": "message_publish",
            "routing_key": "mock.served",
        }
        assert result.error == "publish failed"
