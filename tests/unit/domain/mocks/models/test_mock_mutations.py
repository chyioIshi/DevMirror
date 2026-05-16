import pytest

from app.domain.mocks import MockInvariantError


class TestMockMutations:
    """Проверяет атомарность мутаций модели Mock."""

    def test_rename_keeps_previous_state_when_new_name_is_invalid(
        self,
        mock_factory,
    ) -> None:
        """Проверяет, что невалидное имя не меняет текущее состояние."""
        mock = mock_factory.create_mock(name="stable-name")

        with pytest.raises(MockInvariantError):
            mock.rename("   ")

        assert mock.name == "stable-name"

    def test_change_route_keeps_previous_state_when_new_path_is_invalid(
        self,
        mock_factory,
    ) -> None:
        """Проверяет, что невалидный path не меняет текущий маршрут."""
        mock = mock_factory.create_mock(path="/stable")

        with pytest.raises(MockInvariantError):
            mock.change_route(path="", method=mock.method)

        assert mock.path == "/stable"
