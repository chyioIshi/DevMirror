import pytest

from app.application.mocks.use_cases.update_mock import update_mock
from app.domain.shared import HttpMethod, MatchOperator, MatchSource


class TestUpdateMockFields:
    """Проверяет обновление полей мока."""

    @pytest.mark.asyncio
    async def test_updates_basic_fields(
        self,
        fake_mock_repository,
        mock_factory,
        command_factory,
    ) -> None:
        """Проверяет обновление простых полей."""
        saved_mock = await fake_mock_repository.add(
            mock_factory.create_mock(
                name="old-name",
                description="old-description",
                priority=1,
                scope="old-scope",
                mock_session_id="old-session",
                tags=["old"],
            ),
        )
        command = command_factory.update_mock(
            mock_id=saved_mock.id,
            name="new-name",
            description="new-description",
            priority=10,
            scope="new-scope",
            mock_session_id="new-session",
            tags=["new", "tag"],
        )

        updated_mock = await update_mock(command, fake_mock_repository)

        assert updated_mock.name == "new-name"
        assert updated_mock.description == "new-description"
        assert updated_mock.priority == 10
        assert updated_mock.scope == "new-scope"
        assert updated_mock.mock_session_id == "new-session"
        assert updated_mock.tags == ["new", "tag"]

    @pytest.mark.asyncio
    async def test_updates_route_preserving_missing_method(
        self,
        fake_mock_repository,
        mock_factory,
        command_factory,
    ) -> None:
        """Проверяет обновление пути без изменения метода."""
        saved_mock = await fake_mock_repository.add(
            mock_factory.create_mock(path="/old", method=HttpMethod.GET),
        )
        command = command_factory.update_mock(
            mock_id=saved_mock.id,
            path="/new",
        )

        updated_mock = await update_mock(command, fake_mock_repository)

        assert updated_mock.path == "/new"
        assert updated_mock.method == HttpMethod.GET

    @pytest.mark.asyncio
    async def test_updates_route_preserving_missing_path(
        self,
        fake_mock_repository,
        mock_factory,
        command_factory,
    ) -> None:
        """Проверяет обновление метода без изменения пути."""
        saved_mock = await fake_mock_repository.add(
            mock_factory.create_mock(path="/old", method=HttpMethod.GET),
        )
        command = command_factory.update_mock(
            mock_id=saved_mock.id,
            method=HttpMethod.POST,
        )

        updated_mock = await update_mock(command, fake_mock_repository)

        assert updated_mock.path == "/old"
        assert updated_mock.method == HttpMethod.POST

    @pytest.mark.asyncio
    async def test_updates_response_and_match_rules(
        self,
        fake_mock_repository,
        mock_factory,
        command_factory,
    ) -> None:
        """Проверяет обновление ответа и правил матчинга."""
        saved_mock = await fake_mock_repository.add(mock_factory.create_mock())
        new_response = mock_factory.create_mock(
            response_status_code=201,
            response_headers={"x-response": "ok"},
            response_body={"ok": True},
        ).response
        new_rules = [
            mock_factory.match_rule(
                source=MatchSource.QUERY,
                key="mode",
                operator=MatchOperator.EQ,
                expected="test",
            ),
        ]
        command = command_factory.update_mock(
            mock_id=saved_mock.id,
            response=new_response,
            match_rules=new_rules,
        )

        updated_mock = await update_mock(command, fake_mock_repository)

        assert updated_mock.response.status_code == 201
        assert updated_mock.response.headers == {"x-response": "ok"}
        assert updated_mock.response.body == {"ok": True}
        assert updated_mock.match_rules == new_rules
