from app.domain.mocks.policies import MockActivationPolicy


class TestMockActivationPolicy:
    """Проверяет политику конфликтов при активации."""

    def test_resolve_conflicts_returns_active_conflicts_except_target(
        self,
        mock_factory,
    ) -> None:
        """Проверяет, что остаются только активные конфликты
        не равные target."""
        target = mock_factory.create_mock(mock_id="target", active=False)
        active_conflict = mock_factory.create_mock(mock_id="active", active=True)
        inactive_conflict = mock_factory.create_mock(mock_id="inactive", active=False)
        same_as_target = mock_factory.create_mock(mock_id="target", active=True)

        result = MockActivationPolicy().resolve_conflicts(
            target,
            [active_conflict, inactive_conflict, same_as_target],
        )

        assert result == [active_conflict]
