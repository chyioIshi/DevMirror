from app.domain.shared import HttpMethod


class TestMockLifecycle:
    """Проверяет успешные изменения агрегата Mock."""

    def test_mutations_update_state_and_timestamp(self, mock_factory) -> None:
        """Проверяет изменение основных полей и updated_at."""
        mock = mock_factory.create_mock(
            name="before",
            path="/before",
            method=HttpMethod.GET,
            scope="global",
            priority=0,
            tags=["old"],
        )
        previous_updated_at = mock.updated_at
        response = mock_factory.create_mock(response_status_code=201).response
        rule = mock_factory.match_rule()

        mock.rename("after")
        mock.set_description("description")
        mock.change_route(path="/after", method=HttpMethod.POST)
        mock.change_scope("user-a")
        mock.change_priority(5)
        mock.set_tags(["new"])
        mock.replace_response(response)
        mock.replace_match_rules([rule])

        assert mock.name == "after"
        assert mock.description == "description"
        assert mock.path == "/after"
        assert mock.method == HttpMethod.POST
        assert mock.scope == "user-a"
        assert mock.priority == 5
        assert mock.tags == ["new"]
        assert mock.response == response
        assert mock.match_rules == [rule]
        assert mock.updated_at >= previous_updated_at

    def test_activate_and_deactivate_toggle_active_flag(self, mock_factory) -> None:
        """Проверяет переключение состояния active."""
        mock = mock_factory.create_mock(active=False)

        mock.activate()
        assert mock.active is True

        mock.deactivate()
        assert mock.active is False

    def test_conflicts_with_requires_same_signature_and_different_id(
        self,
        mock_factory,
    ) -> None:
        """Проверяет сигнатуру конфликта между моками."""
        target = mock_factory.create_mock(mock_id="target")
        same_signature = mock_factory.create_mock(mock_id="other")
        same_id = mock_factory.create_mock(mock_id="target")
        different_scope = mock_factory.create_mock(mock_id="scoped", scope="user-b")

        assert target.conflicts_with(same_signature) is True
        assert target.conflicts_with(same_id) is False
        assert target.conflicts_with(different_scope) is False
