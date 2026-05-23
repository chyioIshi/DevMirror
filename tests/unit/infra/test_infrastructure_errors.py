from app.infra.exceptions import (
    DatabaseConnectionError,
    InfrastructureError,
    InfrastructureErrorCode,
    RepositoryError,
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
