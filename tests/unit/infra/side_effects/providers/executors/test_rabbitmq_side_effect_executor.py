import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ClassVar

import pytest

from app.infra.exceptions import InvalidSideEffectProviderConfigError, RabbitMQPublishError
from app.infra.side_effects import ConnectionConfig
from app.infra.side_effects.providers import AsyncRabbitMQSideEffectExecutor


@dataclass(slots=True)
class FakeRabbitMQMessage:
    body: bytes
    headers: dict[str, str] | None
    content_type: str
    delivery_mode: int
    message_id: str | None
    correlation_id: str | None


@dataclass(slots=True)
class PublishedRabbitMQMessage:
    message: FakeRabbitMQMessage
    routing_key: str
    timeout: float | None


@dataclass(slots=True)
class FakeRabbitMQExchange:
    name: str
    exchange_type: str = "topic"
    durable: bool = True
    publish_error: ClassVar[Exception | None] = None

    published_messages: list[PublishedRabbitMQMessage] = field(default_factory=list)

    async def publish(
        self,
        message: FakeRabbitMQMessage,
        *,
        routing_key: str,
        timeout: float | None = None,
    ) -> None:
        if type(self).publish_error is not None:
            raise type(self).publish_error
        self.published_messages.append(
            PublishedRabbitMQMessage(
                message=message,
                routing_key=routing_key,
                timeout=timeout,
            )
        )


@dataclass(slots=True)
class FakeRabbitMQChannel:
    default_exchange: FakeRabbitMQExchange = field(
        default_factory=lambda: FakeRabbitMQExchange(name="")
    )
    closed: bool = False
    exchanges: dict[str, FakeRabbitMQExchange] = field(default_factory=dict)

    async def get_exchange(self, name: str, *, ensure: bool = True) -> FakeRabbitMQExchange:
        _ = ensure
        exchange = FakeRabbitMQExchange(name=name)
        self.exchanges[name] = exchange
        return exchange

    async def declare_exchange(
        self,
        name: str,
        *,
        type: str,
        durable: bool,
    ) -> FakeRabbitMQExchange:
        exchange = FakeRabbitMQExchange(name=name, exchange_type=type, durable=durable)
        self.exchanges[name] = exchange
        return exchange

    async def close(self) -> None:
        self.closed = True


@dataclass(slots=True)
class FakeRabbitMQConnection:
    created_connections: ClassVar[list["FakeRabbitMQConnection"]] = []
    connect_error: ClassVar[Exception | None] = None
    channel_error: ClassVar[Exception | None] = None
    close_error_urls: ClassVar[set[str]] = set()

    url: str
    timeout: float | None
    channel_instance: FakeRabbitMQChannel = field(default_factory=FakeRabbitMQChannel)
    closed: bool = False

    def __post_init__(self) -> None:
        type(self).created_connections.append(self)

    async def channel(self) -> FakeRabbitMQChannel:
        if type(self).channel_error is not None:
            raise type(self).channel_error
        return self.channel_instance

    async def close(self) -> None:
        self.closed = True
        if self.url in type(self).close_error_urls:
            raise RuntimeError(f"close failed: {self.url}")


class FakeDeliveryMode:
    NOT_PERSISTENT = 1
    PERSISTENT = 2


class TestAsyncRabbitMQSideEffectExecutor:
    @pytest.fixture(autouse=True)
    def reset_fake_aio_pika(self, monkeypatch: pytest.MonkeyPatch) -> None:
        FakeRabbitMQConnection.created_connections.clear()
        FakeRabbitMQConnection.connect_error = None
        FakeRabbitMQConnection.channel_error = None
        FakeRabbitMQConnection.close_error_urls = set()
        FakeRabbitMQExchange.publish_error = None

        async def connect_robust(
            url: str,
            *,
            timeout: float | None = None,
        ) -> FakeRabbitMQConnection:
            if FakeRabbitMQConnection.connect_error is not None:
                raise FakeRabbitMQConnection.connect_error
            return FakeRabbitMQConnection(url=url, timeout=timeout)

        monkeypatch.setattr(
            "app.infra.side_effects.providers.executors.rabbitmq_side_effect_executor.aio_pika.connect_robust",
            connect_robust,
        )
        monkeypatch.setattr(
            "app.infra.side_effects.providers.executors.rabbitmq_side_effect_executor.aio_pika.Message",
            FakeRabbitMQMessage,
        )
        monkeypatch.setattr(
            "app.infra.side_effects.providers.executors.rabbitmq_side_effect_executor.aio_pika.DeliveryMode",
            FakeDeliveryMode,
        )

    @pytest.fixture
    def rabbitmq_connection(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> ConnectionConfig:
        return connection_factory(
            name="main-rabbitmq",
            provider="rabbitmq",
            dsn=None,
            settings={
                "url": "amqp://guest:guest@localhost:5672/",
                "exchange": "mock.events",
                "exchange_type": "topic",
                "timeout_seconds": 5,
            },
        )

    async def test_missing_url_raises_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        connection = connection_factory(
            name="main-rabbitmq",
            provider="rabbitmq",
            dsn=None,
            settings={},
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="connection.settings.url must be configured",
        ):
            await executor.publish(
                connection=connection,
                routing_key="mock.served",
                payload={"ok": True},
            )

    async def test_invalid_exchange_type_raises_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        connection = connection_factory(
            name="main-rabbitmq",
            provider="rabbitmq",
            dsn=None,
            settings={
                "url": "amqp://guest:guest@localhost:5672/",
                "exchange_type": "invalid",
            },
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="exchange_type must be direct, topic, fanout, or headers",
        ):
            await executor.publish(
                connection=connection,
                routing_key="mock.served",
                payload={"ok": True},
            )

    @pytest.mark.parametrize(
        ("field", "value", "error"),
        [
            ("timeout_seconds", 0, "connection.settings.timeout_seconds must be a positive number"),
            ("declare_exchange", "yes", "connection.settings.declare_exchange must be a boolean"),
            ("durable_exchange", "yes", "connection.settings.durable_exchange must be a boolean"),
        ],
    )
    async def test_invalid_config_values_raise_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
        field: str,
        value: object,
        error: str,
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        connection = connection_factory(
            name="main-rabbitmq",
            provider="rabbitmq",
            dsn=None,
            settings={
                "url": "amqp://guest:guest@localhost:5672/",
                field: value,
            },
        )

        with pytest.raises(InvalidSideEffectProviderConfigError, match=error):
            await executor.publish(
                connection=connection,
                routing_key="mock.served",
                payload={"ok": True},
            )

    async def test_serializes_supported_payload_values(
        self,
        rabbitmq_connection: ConnectionConfig,
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()

        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="dict",
            payload={"id": "item-1"},
        )
        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="list",
            payload=["item-1"],
        )
        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="string",
            payload="text",
        )
        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="bytes",
            payload=b"bytes",
        )
        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="null",
            payload=None,
        )

        exchange = FakeRabbitMQConnection.created_connections[0].channel_instance.exchanges[
            "mock.events"
        ]
        assert [message.message.body for message in exchange.published_messages] == [
            b'{"id":"item-1"}',
            b'["item-1"]',
            b"text",
            b"bytes",
            b"null",
        ]

    async def test_sets_message_properties(
        self,
        rabbitmq_connection: ConnectionConfig,
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()

        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="mock.served",
            payload={"ok": True},
            headers={"source": "devmirror"},
            content_type="application/vnd.devmirror.event+json",
            delivery_mode="transient",
            message_id="message-1",
            correlation_id="correlation-1",
        )

        exchange = FakeRabbitMQConnection.created_connections[0].channel_instance.exchanges[
            "mock.events"
        ]
        message = exchange.published_messages[0].message
        assert message.headers == {"source": "devmirror"}
        assert message.content_type == "application/vnd.devmirror.event+json"
        assert message.delivery_mode == FakeDeliveryMode.NOT_PERSISTENT
        assert message.message_id == "message-1"
        assert message.correlation_id == "correlation-1"

    async def test_uses_default_exchange_when_exchange_is_empty(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        connection = connection_factory(
            name="main-rabbitmq",
            provider="rabbitmq",
            dsn=None,
            settings={"url": "amqp://guest:guest@localhost:5672/"},
        )

        result = await executor.publish(
            connection=connection,
            routing_key="queue-name",
            payload={"ok": True},
        )

        channel = FakeRabbitMQConnection.created_connections[0].channel_instance
        assert result["exchange"] == ""
        assert channel.default_exchange.published_messages[0].routing_key == "queue-name"
        assert channel.exchanges == {}

    async def test_declares_exchange_when_enabled(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        connection = connection_factory(
            name="main-rabbitmq",
            provider="rabbitmq",
            dsn=None,
            settings={
                "url": "amqp://guest:guest@localhost:5672/",
                "exchange": "mock.events",
                "exchange_type": "fanout",
                "declare_exchange": True,
                "durable_exchange": False,
            },
        )

        await executor.publish(
            connection=connection,
            routing_key="mock.served",
            payload={"ok": True},
        )

        exchange = FakeRabbitMQConnection.created_connections[0].channel_instance.exchanges[
            "mock.events"
        ]
        assert exchange.exchange_type == "fanout"
        assert exchange.durable is False

    async def test_wraps_serialization_failure(
        self,
        rabbitmq_connection: ConnectionConfig,
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()

        with pytest.raises(RabbitMQPublishError) as exc_info:
            await executor.publish(
                connection=rabbitmq_connection,
                routing_key="mock.served",
                payload=object(),
            )

        assert exc_info.value.details == {
            "stage": "serialization",
            "connection": "main-rabbitmq",
        }

    async def test_wraps_connection_failure(
        self,
        rabbitmq_connection: ConnectionConfig,
    ) -> None:
        FakeRabbitMQConnection.connect_error = RuntimeError("connect failed")
        executor = AsyncRabbitMQSideEffectExecutor()

        with pytest.raises(RabbitMQPublishError) as exc_info:
            await executor.publish(
                connection=rabbitmq_connection,
                routing_key="mock.served",
                payload={"ok": True},
            )

        assert exc_info.value.details == {"stage": "connect", "connection": "main-rabbitmq"}

    async def test_wraps_publish_failure(
        self,
        rabbitmq_connection: ConnectionConfig,
    ) -> None:
        FakeRabbitMQExchange.publish_error = RuntimeError("publish failed")
        executor = AsyncRabbitMQSideEffectExecutor()

        with pytest.raises(RabbitMQPublishError) as exc_info:
            await executor.publish(
                connection=rabbitmq_connection,
                routing_key="mock.served",
                payload={"ok": True},
            )

        assert exc_info.value.details == {
            "stage": "publish",
            "connection": "main-rabbitmq",
            "exchange": "mock.events",
            "routing_key": "mock.served",
        }

    async def test_creates_connection_once_for_same_settings(
        self,
        rabbitmq_connection: ConnectionConfig,
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()

        await asyncio.gather(
            *[
                executor.publish(
                    connection=rabbitmq_connection,
                    routing_key="mock.served",
                    payload={"index": index},
                )
                for index in range(5)
            ]
        )

        assert len(FakeRabbitMQConnection.created_connections) == 1

    async def test_reuses_cached_connection(
        self,
        rabbitmq_connection: ConnectionConfig,
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()

        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="first",
            payload={"first": True},
        )
        await executor.publish(
            connection=rabbitmq_connection,
            routing_key="second",
            payload={"second": True},
        )

        exchange = FakeRabbitMQConnection.created_connections[0].channel_instance.exchanges[
            "mock.events"
        ]
        assert len(FakeRabbitMQConnection.created_connections) == 1
        assert [message.routing_key for message in exchange.published_messages] == [
            "first",
            "second",
        ]

    async def test_creates_different_connections_for_different_settings(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        connections = [
            connection_factory(
                name="first-rabbitmq",
                provider="rabbitmq",
                dsn=None,
                settings={"url": "amqp://localhost:5672/", "exchange": "first"},
            ),
            connection_factory(
                name="second-rabbitmq",
                provider="rabbitmq",
                dsn=None,
                settings={"url": "amqp://localhost:5673/", "exchange": "first"},
            ),
            connection_factory(
                name="third-rabbitmq",
                provider="rabbitmq",
                dsn=None,
                settings={"url": "amqp://localhost:5672/", "exchange": "second"},
            ),
        ]

        for connection in connections:
            await executor.publish(
                connection=connection,
                routing_key="mock.served",
                payload={"ok": True},
            )

        assert len(FakeRabbitMQConnection.created_connections) == 3

    async def test_aclose_closes_all_resources_and_clears_cache(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        for connection in [
            connection_factory(
                name="first-rabbitmq",
                provider="rabbitmq",
                dsn=None,
                settings={"url": "amqp://localhost:5672/", "exchange": "first"},
            ),
            connection_factory(
                name="second-rabbitmq",
                provider="rabbitmq",
                dsn=None,
                settings={"url": "amqp://localhost:5673/", "exchange": "second"},
            ),
        ]:
            await executor.publish(
                connection=connection,
                routing_key="mock.served",
                payload={"ok": True},
            )

        await executor.aclose()

        assert [item.closed for item in FakeRabbitMQConnection.created_connections] == [
            True,
            True,
        ]
        assert [
            item.channel_instance.closed for item in FakeRabbitMQConnection.created_connections
        ] == [True, True]
        assert executor._resources == {}

    async def test_aclose_attempts_all_closes_and_clears_cache_when_close_fails(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncRabbitMQSideEffectExecutor()
        for connection in [
            connection_factory(
                name="first-rabbitmq",
                provider="rabbitmq",
                dsn=None,
                settings={"url": "amqp://localhost:5672/", "exchange": "first"},
            ),
            connection_factory(
                name="second-rabbitmq",
                provider="rabbitmq",
                dsn=None,
                settings={"url": "amqp://localhost:5673/", "exchange": "second"},
            ),
        ]:
            await executor.publish(
                connection=connection,
                routing_key="mock.served",
                payload={"ok": True},
            )
        FakeRabbitMQConnection.close_error_urls = {"amqp://localhost:5673/"}

        with pytest.raises(RabbitMQPublishError) as exc_info:
            await executor.aclose()

        assert [item.closed for item in FakeRabbitMQConnection.created_connections] == [
            True,
            True,
        ]
        assert executor._resources == {}
        assert exc_info.value.details["stage"] == "close"
        assert exc_info.value.details["errors"] == ["close failed: amqp://localhost:5673/"]
