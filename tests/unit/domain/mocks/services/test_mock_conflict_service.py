from app.domain.mocks.services import MockConflictService
from app.domain.shared import HttpMethod


class TestMockConflictService:
    """Проверяет поиск конфликтующих моков."""

    def test_find_conflicts_returns_only_same_signature_mocks(self, mock_factory) -> None:
        """Проверяет, что конфликт определяется по route, scope и правилам."""
        target = mock_factory.create_mock(mock_id="target", path="/users", scope="user")
        same_signature = mock_factory.create_mock(
            mock_id="same",
            path="/users",
            scope="user",
        )
        different_path = mock_factory.create_mock(
            mock_id="different-path",
            path="/orders",
            scope="user",
        )
        different_method = mock_factory.create_mock(
            mock_id="different-method",
            path="/users",
            method=HttpMethod.POST,
            scope="user",
        )

        result = MockConflictService().find_conflicts(
            target,
            [same_signature, different_path, different_method],
        )

        assert result == [same_signature]
