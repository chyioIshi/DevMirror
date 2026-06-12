import pytest

from app.infra.exceptions import ConnectionNotFoundError
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry


class TestConnectionRegistry:
    def test_get_connection_by_name(self) -> None:
        connection = ConnectionConfig(
            name="main-kafka",
            provider="kafka",
            settings={"bootstrap_servers": "localhost:9092"},
        )
        registry = ConnectionRegistry(connections=[connection])

        result = registry.get("main-kafka")

        assert result is connection

    def test_get_unknown_connection_raises_clear_error(self) -> None:
        registry = ConnectionRegistry()

        with pytest.raises(ConnectionNotFoundError) as exc_info:
            registry.get("missing")

        assert str(exc_info.value) == "Connection was not found"
        assert exc_info.value.details == {"name": "missing"}

    def test_list_by_provider_returns_only_matching_connection_type(self) -> None:
        kafka_connection = ConnectionConfig(
            name="main-kafka",
            provider="kafka",
            settings={"bootstrap_servers": "localhost:9092"},
        )
        postgres_connection = ConnectionConfig(
            name="main-postgres",
            provider="postgres",
            settings={"dsn": "postgresql://localhost:5432/devmirror"},
        )
        registry = ConnectionRegistry(
            connections=[
                kafka_connection,
                postgres_connection,
            ],
        )

        result = registry.list_by_provider("kafka")

        assert result == [kafka_connection]
