"""Доменные исключения и коды ошибок для моков."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DomainErrorCode(StrEnum):
    """Коды ошибок доменного слоя моков."""

    MOCK_INVARIANT_ERROR = "MOCK_INVARIANT_ERROR"
    INVALID_MOCK_ROUTE = "INVALID_MOCK_ROUTE"
    INVALID_MOCK_STATE = "INVALID_MOCK_STATE"
    INVALID_MATCH_RULE = "INVALID_MATCH_RULE"
    INVALID_MOCK_RESPONSE = "INVALID_MOCK_RESPONSE"
    INVALID_SCOPE = "INVALID_SCOPE"
    MOCK_CONFLICT = "MOCK_CONFLICT"


@dataclass(eq=False)
class DomainError(Exception):
    """Базовая доменная ошибка."""

    code: DomainErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Инициализирует базовый `Exception` сообщением доменной ошибки."""
        Exception.__init__(self, self.message)


class MockInvariantError(DomainError):
    """Ошибка нарушения инварианта агрегата Mock."""

    def __init__(
        self,
        message: str = "Mock invariant was violated",
        details: dict[str, Any] | None = None,
        *,
        code: DomainErrorCode = DomainErrorCode.MOCK_INVARIANT_ERROR,
    ) -> None:
        """Создает ошибку нарушения инварианта мока.

        Args:
            message: Описание ошибки.
            details: Дополнительные детали ошибки.
            code: Код доменной ошибки.
        """
        super().__init__(code=code, message=message, details=details or {})


class InvalidMockRouteError(MockInvariantError):
    """Ошибка некорректного маршрута мока."""

    def __init__(
        self,
        message: str = "Mock route is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Создает ошибку некорректного маршрута мока.

        Args:
            message: Описание ошибки.
            details: Дополнительные детали ошибки.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MOCK_ROUTE,
        )


class InvalidMockStateError(MockInvariantError):
    """Ошибка некорректного состояния мока."""

    def __init__(
        self,
        message: str = "Mock state is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Создает ошибку некорректного состояния мока.

        Args:
            message: Описание ошибки.
            details: Дополнительные детали ошибки.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MOCK_STATE,
        )


class InvalidMatchRuleError(MockInvariantError):
    """Ошибка некорректного правила сопоставления запроса."""

    def __init__(
        self,
        message: str = "Match rule is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Создает ошибку некорректного правила сопоставления.

        Args:
            message: Описание ошибки.
            details: Дополнительные детали ошибки.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MATCH_RULE,
        )


class InvalidMockResponseError(MockInvariantError):
    """Ошибка некорректного ответа мока."""

    def __init__(
        self,
        message: str = "Mock response is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Создает ошибку некорректного ответа мока.

        Args:
            message: Описание ошибки.
            details: Дополнительные детали ошибки.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MOCK_RESPONSE,
        )


class InvalidScopeError(MockInvariantError):
    """Ошибка некорректного scope мока."""

    def __init__(
        self,
        message: str = "Mock scope is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Создает ошибку некорректного scope мока.

        Args:
            message: Описание ошибки.
            details: Дополнительные детали ошибки.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_SCOPE,
        )


class MockConflictError(DomainError):
    """Ошибка конфликта между моками."""

    def __init__(
        self,
        message: str = "Mock conflicts with an existing mock",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Создает ошибку конфликта между моками.

        Args:
            message: Описание ошибки.
            details: Дополнительные детали ошибки.
        """
        super().__init__(
            code=DomainErrorCode.MOCK_CONFLICT,
            message=message,
            details=details or {},
        )
