from app.config import AppSettings
from app.di import providers
from app.di.container import AppContainer
from app.infra.side_effects import ConnectionConfig


class FakeHttpClient:
    def __init__(self) -> None:
        self.is_closed = False

    async def aclose(self) -> None:
        self.is_closed = True


class FakeKafkaProducer:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakePostgresClient:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeRedisClient:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class TestDependencyProviders:
    """Проверяет DI provider-функции."""

    def test_get_app_settings_returns_container_settings(self) -> None:
        """Проверяет получение настроек приложения."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_app_settings(container)

        assert result is container.settings

    def test_get_mock_management_service_returns_container_service(self) -> None:
        """Проверяет получение сервиса управления моками."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_mock_management_service(container)

        assert result is container.mock_management_service

    def test_get_mock_resolver_service_returns_container_service(self) -> None:
        """Проверяет получение сервиса резолва моков."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_mock_resolver_service(container)

        assert result is container.mock_resolver_service

    def test_get_mock_response_builder_returns_container_builder(self) -> None:
        """Проверяет получение билдера HTTP-ответов."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_mock_response_builder(container)

        assert result is container.mock_response_builder

    def test_get_side_effect_execution_service_returns_container_service(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = providers.get_side_effect_execution_service(container)

        assert result is container.side_effect_execution_service

    def test_connection_registry_uses_settings_connections(self) -> None:
        connection = ConnectionConfig(
            name="main-kafka",
            provider="kafka",
            settings={"bootstrap_servers": "localhost:9092"},
        )
        container = AppContainer(
            settings=AppSettings(side_effect_connections=[connection]),
        )

        result = container.connection_registry.get("main-kafka")

        assert result == connection

    def test_side_effect_provider_registry_registers_http_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("http")

        assert result.provider == "http"

    def test_side_effect_provider_registry_registers_kafka_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("kafka")

        assert result.provider == "kafka"

    def test_side_effect_provider_registry_registers_postgres_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("postgres")

        assert result.provider == "postgres"

    def test_side_effect_provider_registry_registers_redis_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("redis")

        assert result.provider == "redis"

    async def test_aclose_closes_side_effect_clients(self, monkeypatch) -> None:
        clients: list[FakeHttpClient] = []
        producers: list[FakeKafkaProducer] = []
        pg_clients: list[FakePostgresClient] = []
        redis_clients: list[FakeRedisClient] = []

        def client_factory() -> FakeHttpClient:
            client = FakeHttpClient()
            clients.append(client)
            return client

        def producer_factory() -> FakeKafkaProducer:
            producer = FakeKafkaProducer()
            producers.append(producer)
            return producer

        def pg_client_factory() -> FakePostgresClient:
            pg_client = FakePostgresClient()
            pg_clients.append(pg_client)
            return pg_client

        def redis_client_factory() -> FakeRedisClient:
            redis_client = FakeRedisClient()
            redis_clients.append(redis_client)
            return redis_client

        monkeypatch.setattr("app.di.container.httpx.AsyncClient", client_factory)
        monkeypatch.setattr("app.di.container.AsyncKafkaProducer", producer_factory)
        monkeypatch.setattr(
            "app.di.container.AsyncPostgresClient",
            pg_client_factory,
        )
        monkeypatch.setattr("app.di.container.AsyncRedisClient", redis_client_factory)
        container = AppContainer(settings=AppSettings())

        container.side_effect_provider_registry.get("http")
        container.side_effect_provider_registry.get("kafka")
        container.side_effect_provider_registry.get("postgres")
        container.side_effect_provider_registry.get("redis")
        await container.aclose()

        assert len(clients) == 1
        assert clients[0].is_closed is True
        assert len(producers) == 1
        assert producers[0].closed is True
        assert len(pg_clients) == 1
        assert pg_clients[0].closed is True
        assert len(redis_clients) == 1
        assert redis_clients[0].closed is True

    def test_get_request_log_service_returns_container_service(self) -> None:
        """Проверяет получение сервиса журнала запросов."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_request_log_service(container)

        assert result is container.request_log_service

    def test_get_request_context_resolver_returns_container_resolver(self) -> None:
        """Проверяет получение резолвера контекста запроса."""
        container = AppContainer(settings=AppSettings())

        result = providers.get_request_context_resolver(container)

        assert result is container.request_context_resolver
