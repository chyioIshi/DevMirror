import asyncio
from dataclasses import dataclass, field
from typing import ClassVar

import pytest

from app.infra.exceptions import KafkaPublishError
from app.infra.side_effects.providers import AsyncKafkaSideEffectExecutor


@dataclass(slots=True)
class SentKafkaMessage:
    topic: str
    value: bytes
    key: bytes | None
    headers: list[tuple[str, bytes]] | None


@dataclass(slots=True)
class FakeAioKafkaProducer:
    created_producers: ClassVar[list["FakeAioKafkaProducer"]] = []
    start_error: ClassVar[Exception | None] = None
    send_error: ClassVar[Exception | None] = None
    stop_error_client_ids: ClassVar[set[str | None]] = set()

    bootstrap_servers: str | list[str]
    client_id: str | None = None
    started: bool = False
    stopped: bool = False
    sent_messages: list[SentKafkaMessage] = field(default_factory=list)

    def __post_init__(self) -> None:
        type(self).created_producers.append(self)

    async def start(self) -> None:
        await asyncio.sleep(0)
        if type(self).start_error is not None:
            raise type(self).start_error
        self.started = True

    async def stop(self) -> None:
        self.stopped = True
        if self.client_id in type(self).stop_error_client_ids:
            raise RuntimeError(f"stop failed: {self.client_id}")

    async def send_and_wait(
        self,
        topic: str,
        *,
        value: bytes,
        key: bytes | None = None,
        headers: list[tuple[str, bytes]] | None = None,
    ) -> None:
        if type(self).send_error is not None:
            raise type(self).send_error
        self.sent_messages.append(
            SentKafkaMessage(
                topic=topic,
                value=value,
                key=key,
                headers=headers,
            )
        )


@pytest.fixture(autouse=True)
def reset_fake_kafka_producer(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeAioKafkaProducer.created_producers.clear()
    FakeAioKafkaProducer.start_error = None
    FakeAioKafkaProducer.send_error = None
    FakeAioKafkaProducer.stop_error_client_ids = set()
    monkeypatch.setattr(
        "app.infra.side_effects.providers.executors.kafka_side_effect_executor.AIOKafkaProducer",
        FakeAioKafkaProducer,
    )


class TestAsyncKafkaSideEffectExecutor:
    async def test_creates_producer_once_for_same_bootstrap_servers_and_client_id(
        self,
    ) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        await asyncio.gather(
            *[
                producer.publish(
                    bootstrap_servers="localhost:9092",
                    topic="events",
                    value={"index": index},
                    client_id="devmirror-tests",
                )
                for index in range(5)
            ]
        )

        assert len(FakeAioKafkaProducer.created_producers) == 1
        assert len(FakeAioKafkaProducer.created_producers[0].sent_messages) == 5

    async def test_reuses_producer(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"first": True},
            client_id="devmirror-tests",
        )
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"second": True},
            client_id="devmirror-tests",
        )

        assert len(FakeAioKafkaProducer.created_producers) == 1
        assert len(FakeAioKafkaProducer.created_producers[0].sent_messages) == 2

    async def test_creates_different_producers_for_different_client_id(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"first": True},
            client_id="first-client",
        )
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"second": True},
            client_id="second-client",
        )

        assert [item.client_id for item in FakeAioKafkaProducer.created_producers] == [
            "first-client",
            "second-client",
        ]

    async def test_serializes_dict_list_string_and_bytes_values(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"entity_id": "entity-1"},
        )
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value=["entity-1", "entity-2"],
        )
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value="text",
        )
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value=b"bytes",
        )

        sent_messages = FakeAioKafkaProducer.created_producers[0].sent_messages
        assert [message.value for message in sent_messages] == [
            b'{"entity_id":"entity-1"}',
            b'["entity-1","entity-2"]',
            b"text",
            b"bytes",
        ]

    async def test_serializes_headers_to_kafka_header_tuples(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"ok": True},
            key="entity-1",
            headers={"source": "devmirror", "event": "created"},
        )

        sent_message = FakeAioKafkaProducer.created_producers[0].sent_messages[0]
        assert sent_message.key == b"entity-1"
        assert sent_message.headers == [
            ("source", b"devmirror"),
            ("event", b"created"),
        ]

    async def test_supports_list_bootstrap_servers(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        await producer.publish(
            bootstrap_servers=["kafka-1:9092", "kafka-2:9092"],
            topic="events",
            value={"ok": True},
        )

        assert FakeAioKafkaProducer.created_producers[0].bootstrap_servers == [
            "kafka-1:9092",
            "kafka-2:9092",
        ]

    async def test_rejects_empty_bootstrap_servers(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        with pytest.raises(KafkaPublishError) as exc_info:
            await producer.publish(
                bootstrap_servers=["kafka-1:9092", ""],
                topic="events",
                value={"ok": True},
            )

        assert exc_info.value.details == {
            "stage": "configuration",
            "field": "bootstrap_servers",
        }

    async def test_wraps_start_failures_into_kafka_publish_error(self) -> None:
        FakeAioKafkaProducer.start_error = RuntimeError("start failed")
        producer = AsyncKafkaSideEffectExecutor()

        with pytest.raises(KafkaPublishError) as exc_info:
            await producer.publish(
                bootstrap_servers="localhost:9092",
                topic="events",
                value={"ok": True},
            )

        assert exc_info.value.details == {"stage": "start"}

    async def test_wraps_send_failures_into_kafka_publish_error(self) -> None:
        FakeAioKafkaProducer.send_error = RuntimeError("send failed")
        producer = AsyncKafkaSideEffectExecutor()

        with pytest.raises(KafkaPublishError) as exc_info:
            await producer.publish(
                bootstrap_servers="localhost:9092",
                topic="events",
                value={"ok": True},
            )

        assert exc_info.value.details == {"stage": "send", "topic": "events"}

    async def test_wraps_serialization_failures_into_kafka_publish_error(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()

        with pytest.raises(KafkaPublishError) as exc_info:
            await producer.publish(
                bootstrap_servers="localhost:9092",
                topic="events",
                value=object(),
            )

        assert exc_info.value.details == {"stage": "serialization"}

    async def test_aclose_stops_all_producers_and_clears_cache(self) -> None:
        producer = AsyncKafkaSideEffectExecutor()
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"first": True},
            client_id="first-client",
        )
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"second": True},
            client_id="second-client",
        )

        await producer.aclose()

        assert [item.stopped for item in FakeAioKafkaProducer.created_producers] == [
            True,
            True,
        ]
        assert producer._producers == {}

    async def test_aclose_attempts_all_stops_and_clears_cache_when_stop_fails(
        self,
    ) -> None:
        producer = AsyncKafkaSideEffectExecutor()
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"first": True},
            client_id="first-client",
        )
        await producer.publish(
            bootstrap_servers="localhost:9092",
            topic="events",
            value={"second": True},
            client_id="second-client",
        )
        FakeAioKafkaProducer.stop_error_client_ids = {"first-client"}

        with pytest.raises(KafkaPublishError) as exc_info:
            await producer.aclose()

        assert [item.stopped for item in FakeAioKafkaProducer.created_producers] == [
            True,
            True,
        ]
        assert producer._producers == {}
        assert exc_info.value.details["stage"] == "close"
