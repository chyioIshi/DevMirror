"""Mapper between Mongo mock documents and domain models."""

from beanie import PydanticObjectId

from app.domain.mocks.models import MatchRule, Mock, MockResponse
from app.infra.db.mongo.documents import (
    MatchRuleDocument,
    MockDocument,
    MockResponseDocument,
)


class MockMapper:
    """Converts mocks between Mongo documents and domain models."""

    @staticmethod
    def to_domain(document: MockDocument) -> Mock:
        """Converts a Mongo mock document to a domain model.

        Args:
            document: Mongo mock document.

        Returns:
            Domain mock model.
        """
        return Mock(
            id=str(document.id),
            name=document.name,
            description=document.description,
            path=document.path,
            method=document.method,
            priority=document.priority,
            active=document.active,
            scope=document.scope,
            match_rules=[
                MatchRule(
                    source=rule.source,
                    key=rule.key,
                    operator=rule.operator,
                    expected=rule.expected,
                )
                for rule in document.match_rules
            ],
            response=MockResponse(
                status_code=document.response.status_code,
                headers=document.response.headers,
                body=document.response.body,
            ),
            tags=document.tags,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def to_document(mock: Mock) -> MockDocument:
        """Converts a domain mock model to a Mongo document.

        Args:
            mock: Domain mock model.

        Returns:
            Mongo mock document.
        """
        payload = MockDocument(
            name=mock.name,
            description=mock.description,
            path=mock.path,
            method=mock.method,
            priority=mock.priority,
            active=mock.active,
            scope=mock.scope,
            match_rules=[
                MatchRuleDocument(
                    source=rule.source,
                    key=rule.key,
                    operator=rule.operator,
                    expected=rule.expected,
                )
                for rule in mock.match_rules
            ],
            response=MockResponseDocument(
                status_code=mock.response.status_code,
                headers=mock.response.headers,
                body=mock.response.body,
            ),
            tags=mock.tags,
            created_at=mock.created_at,
            updated_at=mock.updated_at,
        )

        if mock.id:
            payload.id = PydanticObjectId(mock.id)

        return payload
