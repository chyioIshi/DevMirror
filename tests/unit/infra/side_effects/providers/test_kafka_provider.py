from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.exceptions import ConnectionNotFoundError, InvalidSideEffectProviderConfigError
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry
from app.infra.side_effects.providers import KafkaSideEffectProvider


@dataclass(slots=True)
class PublishedMessage:
    bootstrap_servers: str | list[str]
    topic: str
    value: Any
    key: str | None
    headers: dict[str, str] | None
    client_id: str | None


@dataclass(slots=True)
class FakeKafkaProducer:
    published_messages: list[PublishedMessage] = field(default_factory=list)
    error: Exception | None = None

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
        if self.error is not None:
            raise self.error

        self.published_messages.append(
            PublishedMessage(
                bootstrap_servers=bootstrap_servers,
                topic=topic,
                value=value,
                key=key,
                headers=headers,
                client_id=client_id,
            )
        )


class TestKafkaSideEffectProvider:
    async def test_publishes_to_target_destination(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        producer = FakeKafkaProducer()
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "main-kafka", "destination": "events"},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=producer,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details == {
            "connection": "main-kafka",
            "topic": "events",
            "key": None,
            "client_id": "devmirror-tests",
        }
        assert producer.published_messages == [
            PublishedMessage(
                bootstrap_servers="localhost:9092",
                topic="events",
                value={"ok": True},
                key=None,
                headers=None,
                client_id="devmirror-tests",
            )
        ]

    async def test_passes_key_and_headers_from_rendered_options(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        producer = FakeKafkaProducer()
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "main-kafka", "destination": "events"},
            payload_template={"entity_id": "entity-1"},
            options={
                "key": "entity-1",
                "headers": {
                    "source": "devmirror",
                    "event": "created",
                },
            },
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=producer,
        )

        await provider.execute(effect, side_effect_context)

        assert producer.published_messages[0].key == "entity-1"
        assert producer.published_messages[0].headers == {
            "source": "devmirror",
            "event": "created",
        }
        assert producer.published_messages[0].value == {"entity_id": "entity-1"}

    async def test_uses_named_connection(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="secondary-kafka",
                    provider="kafka",
                    settings={"bootstrap_servers": "secondary:9092"},
                )
            ]
        )
        producer = FakeKafkaProducer()
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "secondary-kafka", "destination": "events"},
        )
        provider = KafkaSideEffectProvider(connection_registry=registry, producer=producer)

        await provider.execute(effect, side_effect_context)

        assert producer.published_messages[0].bootstrap_servers == "secondary:9092"

    async def test_supports_list_bootstrap_servers(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="cluster-kafka",
                    provider="kafka",
                    settings={
                        "bootstrap_servers": ["kafka-1:9092", "kafka-2:9092"],
                    },
                )
            ]
        )
        producer = FakeKafkaProducer()
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "cluster-kafka", "destination": "events"},
        )
        provider = KafkaSideEffectProvider(connection_registry=registry, producer=producer)

        await provider.execute(effect, side_effect_context)

        assert producer.published_messages[0].bootstrap_servers == [
            "kafka-1:9092",
            "kafka-2:9092",
        ]

    async def test_converts_numeric_key_to_string(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        producer = FakeKafkaProducer()
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "main-kafka", "destination": "events"},
            options={"key": 42},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=producer,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.details["key"] == "42"
        assert producer.published_messages[0].key == "42"

    async def test_invalid_headers_fail_clearly(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "main-kafka", "destination": "events"},
            options={"headers": {"source": 123}},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=FakeKafkaProducer(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="options.headers must contain only string values",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_wrong_side_effect_type_fails_clearly(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.HTTP_CALLBACK,
            provider="kafka",
            target={"connection": "main-kafka"},
            payload_template={},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=FakeKafkaProducer(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="supports only message_publish",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_provider_mismatch_fails_clearly(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="http",
            target={"connection": "main-kafka", "destination": "events"},
            payload_template={},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=FakeKafkaProducer(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="provider must match kafka",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_unknown_connection_fails_clearly(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "missing", "destination": "events"},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=FakeKafkaProducer(),
        )

        with pytest.raises(ConnectionNotFoundError) as exc_info:
            await provider.execute(effect, side_effect_context)

        assert exc_info.value.details == {"name": "missing"}

    async def test_mismatched_connection_fails_clearly(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="main-http",
                    provider="http",
                    settings={"bootstrap_servers": "localhost:9092"},
                )
            ]
        )
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "main-http", "destination": "events"},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=registry,
            producer=FakeKafkaProducer(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must reference a kafka connection",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_producer_error_returns_failed_execution_result(
        self,
        kafka_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"connection": "main-kafka", "destination": "events"},
        )
        provider = KafkaSideEffectProvider(
            connection_registry=kafka_connection_registry,
            producer=FakeKafkaProducer(error=RuntimeError("publish failed")),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is False
        assert result.error == "publish failed"
        assert result.details == {"topic": "events", "key": None}

    def test_kafka_client_imports_do_not_leak_into_application_or_domain(self) -> None:
        checked_files = [
            *Path("app/application").rglob("*.py"),
            *Path("app/domain").rglob("*.py"),
        ]
        forbidden_imports = (
            "import aiokafka",
            "from aiokafka",
            "import confluent_kafka",
            "from confluent_kafka",
            "import kafka",
            "from kafka",
        )

        leaked_files = [
            str(path)
            for path in checked_files
            if any(
                forbidden_import in path.read_text(encoding="utf-8")
                for forbidden_import in forbidden_imports
            )
        ]

        assert leaked_files == []
