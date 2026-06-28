from app.infra.exceptions import (
    ConnectionNotFoundError,
    DatabaseConnectionError,
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidSideEffectProviderConfigError,
    MongoSideEffectError,
    PostgresInsertError,
    RabbitMQPublishError,
    RepositoryError,
    SideEffectProviderPluginError,
)


class TestInfrastructureErrors:
    """Проверяет инфраструктурные исключения."""

    def test_infrastructure_error_initializes_exception_message(self) -> None:
        """Проверяет сообщение базового исключения."""
        error = InfrastructureError(
            code=InfrastructureErrorCode.INFRASTRUCTURE_ERROR,
            message="broken",
            details={"field": "value"},
        )

        assert str(error) == "broken"
        assert error.code == InfrastructureErrorCode.INFRASTRUCTURE_ERROR
        assert error.details == {"field": "value"}

    def test_repository_error_uses_default_values(self) -> None:
        """Проверяет значения RepositoryError по умолчанию."""
        error = RepositoryError()

        assert str(error) == "Repository operation failed"
        assert error.code == InfrastructureErrorCode.REPOSITORY_ERROR
        assert error.details == {}

    def test_database_connection_error_keeps_details(self) -> None:
        """Проверяет детали ошибки подключения к базе."""
        error = DatabaseConnectionError(details={"operation": "list"})

        assert str(error) == "Database connection failed"
        assert error.code == InfrastructureErrorCode.DATABASE_CONNECTION_ERROR
        assert error.details == {"operation": "list"}

    def test_side_effect_provider_plugin_error_keeps_details(self) -> None:
        error = SideEffectProviderPluginError(details={"entry_point": "kafka"})

        assert str(error) == "Side effect provider plugin could not be loaded"
        assert error.code == InfrastructureErrorCode.SIDE_EFFECT_PROVIDER_PLUGIN_ERROR
        assert error.details == {"entry_point": "kafka"}

    def test_connection_not_found_error_adds_name(self) -> None:
        error = ConnectionNotFoundError(name="main-kafka")

        assert str(error) == "Connection was not found"
        assert error.code == InfrastructureErrorCode.CONNECTION_NOT_FOUND
        assert error.details == {"name": "main-kafka"}

    def test_invalid_side_effect_provider_config_error_keeps_details(self) -> None:
        error = InvalidSideEffectProviderConfigError(details={"field": "options.method"})

        assert str(error) == "Invalid side effect provider configuration"
        assert error.code == InfrastructureErrorCode.INVALID_SIDE_EFFECT_PROVIDER_CONFIG
        assert error.details == {"field": "options.method"}

    def test_postgres_insert_error_keeps_details(self) -> None:
        error = PostgresInsertError(details={"stage": "execute"})

        assert str(error) == "Postgres insert failed"
        assert error.code == InfrastructureErrorCode.POSTGRES_INSERT_ERROR
        assert error.details == {"stage": "execute"}

    def test_mongo_side_effect_error_keeps_details(self) -> None:
        error = MongoSideEffectError(details={"stage": "execute"})

        assert str(error) == "Mongo side effect execution failed"
        assert error.code == InfrastructureErrorCode.MONGO_SIDE_EFFECT_ERROR
        assert error.details == {"stage": "execute"}

    def test_rabbitmq_publish_error_keeps_details(self) -> None:
        error = RabbitMQPublishError(details={"stage": "publish"})

        assert str(error) == "RabbitMQ message publish failed"
        assert error.code == InfrastructureErrorCode.RABBITMQ_PUBLISH_ERROR
        assert error.details == {"stage": "publish"}
