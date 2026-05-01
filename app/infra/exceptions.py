from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class InfrastructureErrorCode(StrEnum):
    """Коды ошибок инфраструктурного слоя."""

    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    REPOSITORY_ERROR = "REPOSITORY_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    TRANSACTION_ERROR = "TRANSACTION_ERROR"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"


@dataclass(eq=False)
class InfrastructureError(Exception):
    """Базовая инфраструктурная ошибка."""

    code: InfrastructureErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)


class RepositoryError(InfrastructureError):
    """Ошибка выполнения операции репозитория."""

    def __init__(
        self,
        message: str = "Repository operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=InfrastructureErrorCode.REPOSITORY_ERROR,
            message=message,
            details=details or {},
        )

