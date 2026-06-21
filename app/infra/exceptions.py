"""Infrastructure-layer exceptions and error codes."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class InfrastructureErrorCode(StrEnum):
    """Infrastructure-layer error codes."""

    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    REPOSITORY_ERROR = "REPOSITORY_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    TRANSACTION_ERROR = "TRANSACTION_ERROR"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    SIDE_EFFECT_PROVIDER_PLUGIN_ERROR = "SIDE_EFFECT_PROVIDER_PLUGIN_ERROR"
    CONNECTION_NOT_FOUND = "CONNECTION_NOT_FOUND"
    INVALID_SIDE_EFFECT_PROVIDER_CONFIG = "INVALID_SIDE_EFFECT_PROVIDER_CONFIG"
    KAFKA_PUBLISH_ERROR = "KAFKA_PUBLISH_ERROR"
    POSTGRES_INSERT_ERROR = "POSTGRES_INSERT_ERROR"
    REDIS_SIDE_EFFECT_ERROR = "REDIS_SIDE_EFFECT_ERROR"
    MONGO_SIDE_EFFECT_ERROR = "MONGO_SIDE_EFFECT_ERROR"


@dataclass(eq=False)
class InfrastructureError(Exception):
    """Base infrastructure error."""

    code: InfrastructureErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initializes the base `Exception` with the infrastructure error message."""
        Exception.__init__(self, self.message)


class RepositoryError(InfrastructureError):
    """Error raised when a repository operation fails."""

    def __init__(
        self,
        message: str = "Repository operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a repository error.

        Args:
            message: Human-readable error description.
            details: Additional error details.
        """
        super().__init__(
            code=InfrastructureErrorCode.REPOSITORY_ERROR,
            message=message,
            details=details or {},
        )


class DatabaseConnectionError(InfrastructureError):
    """Error raised when a database connection operation fails."""

    def __init__(
        self,
        message: str = "Database connection failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a database connection error.

        Args:
            message: Human-readable error description.
            details: Additional error details.
        """
        super().__init__(
            code=InfrastructureErrorCode.DATABASE_CONNECTION_ERROR,
            message=message,
            details=details or {},
        )


class SideEffectProviderPluginError(InfrastructureError):
    """Error raised when a side effect provider plugin cannot be loaded."""

    def __init__(
        self,
        message: str = "Side effect provider plugin could not be loaded",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a side effect provider plugin loading error."""
        super().__init__(
            code=InfrastructureErrorCode.SIDE_EFFECT_PROVIDER_PLUGIN_ERROR,
            message=message,
            details=details or {},
        )


class ConnectionNotFoundError(InfrastructureError):
    """Error raised when a named side effect provider connection is unknown."""

    def __init__(
        self,
        message: str = "Connection was not found",
        details: dict[str, Any] | None = None,
        *,
        name: str | None = None,
    ) -> None:
        """Creates a connection-not-found error."""
        error_details = dict(details or {})
        if name is not None:
            error_details.setdefault("name", name)
        super().__init__(
            code=InfrastructureErrorCode.CONNECTION_NOT_FOUND,
            message=message,
            details=error_details,
        )


class InvalidSideEffectProviderConfigError(InfrastructureError):
    """Error raised when a side effect provider config is invalid."""

    def __init__(
        self,
        message: str = "Invalid side effect provider configuration",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates an invalid side effect provider config error."""
        super().__init__(
            code=InfrastructureErrorCode.INVALID_SIDE_EFFECT_PROVIDER_CONFIG,
            message=message,
            details=details or {},
        )


class KafkaPublishError(InfrastructureError):
    """Error raised when a Kafka message cannot be published."""

    def __init__(
        self,
        message: str = "Kafka message publish failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a Kafka publish error."""
        super().__init__(
            code=InfrastructureErrorCode.KAFKA_PUBLISH_ERROR,
            message=message,
            details=details or {},
        )


class PostgresInsertError(InfrastructureError):
    """Error raised when a Postgres insert cannot be executed."""

    def __init__(
        self,
        message: str = "Postgres insert failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a Postgres insert error."""
        super().__init__(
            code=InfrastructureErrorCode.POSTGRES_INSERT_ERROR,
            message=message,
            details=details or {},
        )


class RedisSideEffectError(InfrastructureError):
    """Error raised when a Redis side effect command cannot be executed."""

    def __init__(
        self,
        message: str = "Redis side effect execution failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a Redis side effect execution error."""
        super().__init__(
            code=InfrastructureErrorCode.REDIS_SIDE_EFFECT_ERROR,
            message=message,
            details=details or {},
        )


class MongoSideEffectError(InfrastructureError):
    """Error raised when a MongoDB side effect command cannot be executed."""

    def __init__(
        self,
        message: str = "Mongo side effect execution failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a MongoDB side effect execution error."""
        super().__init__(
            code=InfrastructureErrorCode.MONGO_SIDE_EFFECT_ERROR,
            message=message,
            details=details or {},
        )
