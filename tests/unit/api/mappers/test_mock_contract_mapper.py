from app.api.contracts.mocks import CreateMockRequest, UpdateMockRequest
from app.api.contracts.mocks.items import MatchRuleItem, MockResponsePayloadItem
from app.api.mappers import MockContractMapper
from app.application.mocks.commands import UNSET
from app.domain.mocks.models import SideEffect, SideEffectType
from app.domain.shared import HttpMethod, MatchOperator, MatchSource


class TestMockContractMapper:
    """Проверяет маппинг CreateMockRequest в domain model."""

    def test_create_request_maps_to_inactive_mock(self) -> None:
        """Проверяет преобразование CreateMockRequest в неактивный domain mock."""
        request = CreateMockRequest(
            name="test",
            description="description",
            path="/test",
            method=HttpMethod.POST,
            priority=10,
            scope="user_name",
            match_rules=[
                MatchRuleItem(
                    source=MatchSource.HEADER,
                    key="x-user",
                    operator=MatchOperator.EQ,
                    expected="user1",
                ),
            ],
            response=MockResponsePayloadItem(
                status_code=201,
                headers={"x-response": "ok"},
                body={"id": 1},
                side_effects=[
                    {
                        "type": "message_publish",
                        "provider": "kafka",
                        "target": {"topic": "users"},
                        "payload_template": {"id": "{{body.id}}"},
                    },
                ],
            ),
            tags=["users"],
        )

        mock = MockContractMapper.to_domain_mock_model(request)

        assert mock.id is None
        assert mock.name == "test"
        assert mock.description == "description"
        assert mock.path == "/test"
        assert mock.method == HttpMethod.POST
        assert mock.priority == 10
        assert mock.active is False
        assert mock.scope == "user_name"
        assert len(mock.match_rules) == 1
        assert mock.match_rules[0].source == MatchSource.HEADER
        assert mock.match_rules[0].key == "x-user"
        assert mock.match_rules[0].operator == MatchOperator.EQ
        assert mock.match_rules[0].expected == "user1"
        assert mock.response.status_code == 201
        assert mock.response.headers == {"x-response": "ok"}
        assert mock.response.body == {"id": 1}
        assert mock.response.side_effects[0].type == SideEffectType.MESSAGE_PUBLISH
        assert mock.response.side_effects[0].provider == "kafka"
        assert mock.response.side_effects[0].target == {"topic": "users"}
        assert mock.response.side_effects[0].payload_template == {"id": "{{body.id}}"}
        assert mock.tags == ["users"]

    def test_update_request_maps_only_provided_fields(self) -> None:
        """Проверяет маппинг только переданных полей update request."""
        request = UpdateMockRequest(name="new-name", priority=10)

        command = MockContractMapper.to_update_mock_command("mock-1", request)

        assert command.mock_id == "mock-1"
        assert command.name == "new-name"
        assert command.priority == 10
        assert command.description is UNSET
        assert command.path is UNSET
        assert command.method is UNSET
        assert command.scope is UNSET
        assert command.match_rules is UNSET
        assert command.response is UNSET
        assert command.tags is UNSET

    def test_update_request_maps_nested_fields(self) -> None:
        """Проверяет маппинг вложенных полей update request."""
        request = UpdateMockRequest(
            match_rules=[
                MatchRuleItem(
                    source=MatchSource.QUERY,
                    key="mode",
                    operator=MatchOperator.EQ,
                    expected="test",
                ),
            ],
            response=MockResponsePayloadItem(
                status_code=202,
                headers={"x-response": "accepted"},
                body={"accepted": True},
                side_effects=[
                    {
                        "type": "http_callback",
                        "provider": "webhook",
                        "target": {"url": "https://example.test/callback"},
                        "payload_template": {"accepted": "{{body.accepted}}"},
                    },
                ],
            ),
        )

        command = MockContractMapper.to_update_mock_command("mock-1", request)

        assert command.match_rules is not UNSET
        assert command.match_rules[0].source == MatchSource.QUERY
        assert command.match_rules[0].key == "mode"
        assert command.match_rules[0].operator == MatchOperator.EQ
        assert command.match_rules[0].expected == "test"
        assert command.response is not UNSET
        assert command.response.status_code == 202
        assert command.response.headers == {"x-response": "accepted"}
        assert command.response.body == {"accepted": True}
        assert command.response.side_effects[0].type == "http_callback"

    def test_domain_mock_maps_to_response_item(self, mock_factory) -> None:
        """Проверяет маппинг domain mock в response dto."""
        mock = mock_factory.create_mock(
            mock_id="mock-1",
            name="test",
            description="description",
            path="/test",
            method=HttpMethod.POST,
            priority=10,
            active=True,
            scope="user_name",
            match_rules=[
                mock_factory.match_rule(
                    source=MatchSource.HEADER,
                    key="x-user",
                    operator=MatchOperator.EQ,
                    expected="user1",
                ),
            ],
            response_status_code=201,
            response_headers={"x-response": "ok"},
            response_body={"id": 1},
            response_side_effects=[
                SideEffect(
                    type=SideEffectType.MESSAGE_PUBLISH,
                    provider="kafka",
                    target={"topic": "users"},
                    payload_template={"id": "{{body.id}}"},
                ),
            ],
            tags=["users"],
        )

        item = MockContractMapper.from_domain_mock_model(mock)

        assert item.id == "mock-1"
        assert item.name == "test"
        assert item.description == "description"
        assert item.path == "/test"
        assert item.method == HttpMethod.POST
        assert item.priority == 10
        assert item.active is True
        assert item.scope == "user_name"
        assert item.match_rules[0].source == MatchSource.HEADER
        assert item.match_rules[0].key == "x-user"
        assert item.match_rules[0].operator == MatchOperator.EQ
        assert item.match_rules[0].expected == "user1"
        assert item.response.status_code == 201
        assert item.response.headers == {"x-response": "ok"}
        assert item.response.body == {"id": 1}
        assert item.response.side_effects[0].type == SideEffectType.MESSAGE_PUBLISH
        assert item.response.side_effects[0].provider == "kafka"
        assert item.response.side_effects[0].target == {"topic": "users"}
        assert item.response.side_effects[0].payload_template == {"id": "{{body.id}}"}
        assert item.tags == ["users"]
