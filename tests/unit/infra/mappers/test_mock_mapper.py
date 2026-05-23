from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.domain.shared import HttpMethod, MatchOperator, MatchSource
from app.infra.db.mongo.documents import (
    MatchRuleDocument,
    MockDocument,
    MockResponseDocument,
)
from app.infra.mappers.mock_mapper import MockMapper


class TestMockMapper:
    """Проверяет маппинг Mock domain model в Mongo document и обратно."""

    def test_to_document_maps_domain_mock(
        self,
        mock_factory,
        beanie_document_constructors: None,
    ) -> None:
        """Проверяет маппинг Mock domain model в Mongo document."""
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        updated_at = datetime(2026, 1, 2, tzinfo=UTC)
        mock = mock_factory.create_mock(
            mock_id="000000000000000000000001",
            name="users",
            description="desc",
            path="/users",
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
            tags=["users"],
            created_at=created_at,
            updated_at=updated_at,
        )

        document = MockMapper.to_document(mock)

        assert document.id == PydanticObjectId("000000000000000000000001")
        assert document.name == "users"
        assert document.description == "desc"
        assert document.path == "/users"
        assert document.method == HttpMethod.POST
        assert document.priority == 10
        assert document.active is True
        assert document.scope == "user_name"
        assert document.match_rules[0].key == "x-user"
        assert document.response.status_code == 201
        assert document.response.headers == {"x-response": "ok"}
        assert document.response.body == {"id": 1}
        assert document.tags == ["users"]
        assert document.created_at == created_at
        assert document.updated_at == updated_at

    def test_to_domain_maps_mongo_document(
        self,
        beanie_document_constructors: None,
    ) -> None:
        """Проверяет маппинг Mongo document в domain Mock."""
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        updated_at = datetime(2026, 1, 2, tzinfo=UTC)
        document = MockDocument(
            name="users",
            description="desc",
            path="/users",
            method=HttpMethod.POST,
            priority=10,
            active=True,
            scope="user_name",
            match_rules=[
                MatchRuleDocument(
                    source=MatchSource.HEADER,
                    key="x-user",
                    operator=MatchOperator.EQ,
                    expected="user1",
                ),
            ],
            response=MockResponseDocument(
                status_code=201,
                headers={"x-response": "ok"},
                body={"id": 1},
            ),
            tags=["users"],
            created_at=created_at,
            updated_at=updated_at,
        )
        document.id = PydanticObjectId("000000000000000000000001")

        mock = MockMapper.to_domain(document)

        assert mock.id == "000000000000000000000001"
        assert mock.name == "users"
        assert mock.description == "desc"
        assert mock.path == "/users"
        assert mock.method == HttpMethod.POST
        assert mock.priority == 10
        assert mock.active is True
        assert mock.scope == "user_name"
        assert mock.match_rules[0].key == "x-user"
        assert mock.response.status_code == 201
        assert mock.response.headers == {"x-response": "ok"}
        assert mock.response.body == {"id": 1}
        assert mock.tags == ["users"]
        assert mock.created_at == created_at
        assert mock.updated_at == updated_at
