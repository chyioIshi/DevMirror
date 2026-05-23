import pytest

from app.domain.mocks import (
    InvalidMockRouteError,
    InvalidMockStateError,
    InvalidScopeError,
    MockInvariantError,
)


class TestMockInvariants:
    """Проверяет инварианты агрегата Mock."""

    def test_name_must_not_be_blank(self, mock_factory) -> None:
        """Проверяет запрет пустого имени."""
        with pytest.raises(InvalidMockStateError):
            mock_factory.create_mock(name=" ")

    def test_path_must_not_be_blank(self, mock_factory) -> None:
        """Проверяет запрет пустого path."""
        with pytest.raises(InvalidMockRouteError):
            mock_factory.create_mock(path="")

    def test_priority_must_not_be_negative(self, mock_factory) -> None:
        """Проверяет запрет отрицательного priority."""
        with pytest.raises(MockInvariantError):
            mock_factory.create_mock(priority=-1)

    def test_scope_must_not_be_blank(self, mock_factory) -> None:
        """Проверяет запрет пустого scope."""
        with pytest.raises(InvalidScopeError):
            mock_factory.create_mock(scope=" ")
