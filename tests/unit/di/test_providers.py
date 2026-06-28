from app.config import AppSettings
from app.di import providers
from app.di.container import AppContainer
from app.infra.side_effects import ConnectionConfig
from app.infra.side_effects.schedulers import (
    CeleryAsyncTaskScheduler,
    InProcessAsyncTaskScheduler,
)


class FakeHttpClient:
    def __init__(self) -> None:
        self.is_closed = False

    async def aclose(self) -> None:
        self.is_closed = True


class FakeKafkaSideEffectExecutor:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeMongoSideEffectExecutor:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakePostgresSideEffectExecutor:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeRabbitMQSideEffectExecutor:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeRedisSideEffectExecutor:
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

    def test_async_task_scheduler_uses_in_process_adapter_by_default(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.async_task_scheduler

        assert isinstance(result, InProcessAsyncTaskScheduler)

    def test_async_task_scheduler_uses_celery_adapter_when_configured(self) -> None:
        container = AppContainer(settings=AppSettings(async_task_scheduler="celery"))

        result = container.async_task_scheduler

        assert isinstance(result, CeleryAsyncTaskScheduler)

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

    def test_side_effect_provider_registry_registers_mongo_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("mongo")

        assert result.provider == "mongo"

    def test_side_effect_provider_registry_registers_postgres_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("postgres")

        assert result.provider == "postgres"

    def test_side_effect_provider_registry_registers_redis_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("redis")

        assert result.provider == "redis"

    def test_side_effect_provider_registry_registers_rabbitmq_provider(self) -> None:
        container = AppContainer(settings=AppSettings())

        result = container.side_effect_provider_registry.get("rabbitmq")

        assert result.provider == "rabbitmq"

    async def test_aclose_closes_side_effect_executors(self, monkeypatch) -> None:
        clients: list[FakeHttpClient] = []
        kafka_executors: list[FakeKafkaSideEffectExecutor] = []
        mongo_executors: list[FakeMongoSideEffectExecutor] = []
        postgres_executors: list[FakePostgresSideEffectExecutor] = []
        rabbitmq_executors: list[FakeRabbitMQSideEffectExecutor] = []
        redis_executors: list[FakeRedisSideEffectExecutor] = []

        def client_factory() -> FakeHttpClient:
            client = FakeHttpClient()
            clients.append(client)
            return client

        def kafka_executor_factory() -> FakeKafkaSideEffectExecutor:
            executor = FakeKafkaSideEffectExecutor()
            kafka_executors.append(executor)
            return executor

        def mongo_executor_factory() -> FakeMongoSideEffectExecutor:
            executor = FakeMongoSideEffectExecutor()
            mongo_executors.append(executor)
            return executor

        def postgres_executor_factory() -> FakePostgresSideEffectExecutor:
            executor = FakePostgresSideEffectExecutor()
            postgres_executors.append(executor)
            return executor

        def rabbitmq_executor_factory() -> FakeRabbitMQSideEffectExecutor:
            executor = FakeRabbitMQSideEffectExecutor()
            rabbitmq_executors.append(executor)
            return executor

        def redis_executor_factory() -> FakeRedisSideEffectExecutor:
            executor = FakeRedisSideEffectExecutor()
            redis_executors.append(executor)
            return executor

        monkeypatch.setattr("app.di.container.httpx.AsyncClient", client_factory)
        monkeypatch.setattr(
            "app.di.container.AsyncKafkaSideEffectExecutor",
            kafka_executor_factory,
        )
        monkeypatch.setattr(
            "app.di.container.AsyncMongoSideEffectExecutor",
            mongo_executor_factory,
        )
        monkeypatch.setattr(
            "app.di.container.AsyncPostgresSideEffectExecutor",
            postgres_executor_factory,
        )
        monkeypatch.setattr(
            "app.di.container.AsyncRabbitMQSideEffectExecutor",
            rabbitmq_executor_factory,
        )
        monkeypatch.setattr(
            "app.di.container.AsyncRedisSideEffectExecutor",
            redis_executor_factory,
        )
        container = AppContainer(settings=AppSettings())

        container.side_effect_provider_registry.get("http")
        container.side_effect_provider_registry.get("kafka")
        container.side_effect_provider_registry.get("mongo")
        container.side_effect_provider_registry.get("postgres")
        container.side_effect_provider_registry.get("rabbitmq")
        container.side_effect_provider_registry.get("redis")
        await container.aclose()

        assert len(clients) == 1
        assert clients[0].is_closed is True
        assert len(kafka_executors) == 1
        assert kafka_executors[0].closed is True
        assert len(mongo_executors) == 1
        assert mongo_executors[0].closed is True
        assert len(postgres_executors) == 1
        assert postgres_executors[0].closed is True
        assert len(rabbitmq_executors) == 1
        assert rabbitmq_executors[0].closed is True
        assert len(redis_executors) == 1
        assert redis_executors[0].closed is True

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
