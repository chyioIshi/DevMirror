from app.api.contracts.mocks import CreateMockRequest
from app.api.contracts.mocks.items import MatchRuleItem, MockResponsePayloadItem
from app.api.mappers import MockContractMapper
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
        assert mock.tags == ["users"]

