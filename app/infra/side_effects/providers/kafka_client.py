"""aiokafka-backed message producer adapter."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from aiokafka import AIOKafkaProducer

from app.infra.exceptions import KafkaPublishError

_BOOTSTRAP_SERVERS_ERROR = (
    "Kafka bootstrap_servers must be a non-empty string or list of non-empty strings"
)


@dataclass(slots=True, frozen=True)
class KafkaProducerKey:
    """Identifies a reusable Kafka producer instance."""

    bootstrap_servers: str | tuple[str, ...]
    client_id: str | None


class AioKafkaMessageProducer:
    """Publishes Kafka messages using reusable aiokafka producers."""

    def __init__(self) -> None:
        """Initializes an empty producer cache."""
        self._producers: dict[KafkaProducerKey, AIOKafkaProducer] = {}
        self._producer_lock = asyncio.Lock()

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
        try:
            serialized_value = self._serialize_value(value)
            serialized_key = self._serialize_optional_string(key)
            serialized_headers = self._serialize_headers(headers)
        except Exception as exc:
            raise KafkaPublishError(
                "Kafka message serialization failed",
                details={"stage": "serialization"},
            ) from exc

        producer = await self._producer(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
        )
        try:
            await producer.send_and_wait(
                topic,
                value=serialized_value,
                key=serialized_key,
                headers=serialized_headers,
            )
        except Exception as exc:
            raise KafkaPublishError(
                "Kafka message send failed",
                details={"stage": "send", "topic": topic},
            ) from exc

    async def aclose(self) -> None:
        """Stops all cached Kafka producers."""
        results: list[object] = []
        try:
            results = await asyncio.gather(
                *(producer.stop() for producer in self._producers.values()),
                return_exceptions=True,
            )
        finally:
            self._producers.clear()

        errors = [str(result) for result in results if isinstance(result, Exception)]
        if errors:
            raise KafkaPublishError(
                "Kafka producer close failed",
                details={"stage": "close", "errors": errors},
            )

    async def _producer(
        self,
        *,
        bootstrap_servers: str | list[str],
        client_id: str | None,
    ) -> AIOKafkaProducer:
        bootstrap_servers = self._validate_bootstrap_servers(bootstrap_servers)
        key = KafkaProducerKey(
            bootstrap_servers=self._producer_key(bootstrap_servers),
            client_id=client_id,
        )
        producer = self._producers.get(key)
        if producer is not None:
            return producer

        async with self._producer_lock:
            producer = self._producers.get(key)
            if producer is not None:
                return producer

            producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap_servers,
                client_id=client_id,
            )
            try:
                await producer.start()
            except Exception as exc:
                raise KafkaPublishError(
                    "Kafka producer start failed",
                    details={"stage": "start"},
                ) from exc

            self._producers[key] = producer
            return producer

    def _validate_bootstrap_servers(
        self,
        bootstrap_servers: str | list[str],
    ) -> str | list[str]:
        if isinstance(bootstrap_servers, str) and bootstrap_servers.strip():
            return bootstrap_servers
        if isinstance(bootstrap_servers, list) and bootstrap_servers:
            for server in bootstrap_servers:
                if not isinstance(server, str) or not server.strip():
                    raise KafkaPublishError(
                        _BOOTSTRAP_SERVERS_ERROR,
                        details={"stage": "configuration", "field": "bootstrap_servers"},
                    )
            return bootstrap_servers
        raise KafkaPublishError(
            _BOOTSTRAP_SERVERS_ERROR,
            details={"stage": "configuration", "field": "bootstrap_servers"},
        )

    def _producer_key(self, bootstrap_servers: str | list[str]) -> str | tuple[str, ...]:
        if isinstance(bootstrap_servers, str):
            return bootstrap_servers
        return tuple(bootstrap_servers)

    def _serialize_value(self, value: Any) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode()
        return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()

    def _serialize_optional_string(self, value: str | None) -> bytes | None:
        if value is None:
            return None
        return value.encode()

    def _serialize_headers(
        self,
        headers: dict[str, str] | None,
    ) -> list[tuple[str, bytes]] | None:
        if headers is None:
            return None
        return [(key, value.encode()) for key, value in headers.items()]
