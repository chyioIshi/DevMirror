
from app.api.contracts.mocks.items import (
    MatchRuleItem,
)
from app.api.contracts.mocks.items import (
    MockResponsePayloadItem as MockResponseItemDTO,
)
from app.api.contracts.mocks.requests import (
    CreateMockRequest,
    UpdateMockRequest,
)
from app.api.contracts.mocks.responses import MockResponseItem
from app.domain.mocks.models.match_rule import MatchRule
from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.mock_response import MockResponse
from app.domain.mocks.models.mock_update import _MISSING, MockUpdate


class MockContractMapper:
    """Преобразует DTO моков в доменные модели и обратно."""

    @staticmethod
    def to_domain_mock_model(request: CreateMockRequest) -> Mock:
        """Преобразует REQUEST DTO создания мока в доменную модель Mock."""
        return Mock(
            name=request.name,
            description=request.description,
            path=request.path,
            method=request.method,
            priority=request.priority,
            active=request.active,
            scope=request.scope,
            match_rules=[
                MockContractMapper.to_domain_match_rule_model(rule)
                for rule in request.match_rules
            ],
            response=MockContractMapper.to_domain_mock_response_model(request.response),
            tags=request.tags,
        )

    @staticmethod
    def to_domain_mock_update_model(request: UpdateMockRequest) -> MockUpdate:
        """Преобразует REQUEST DTO частичного обновления в доменную модель MockUpdate."""
        set_fields = request.model_fields_set
        return MockUpdate(
            name=request.name if "name" in set_fields else _MISSING,
            description=request.description if "description" in set_fields else _MISSING,
            path=request.path if "path" in set_fields else _MISSING,
            method=request.method if "method" in set_fields else _MISSING,
            priority=request.priority if "priority" in set_fields else _MISSING,
            active=request.active if "active" in set_fields else _MISSING,
            scope=request.scope if "scope" in set_fields else _MISSING,
            match_rules=(
                [MockContractMapper.to_domain_match_rule_model(r) for r in request.match_rules]
                if "match_rules" in set_fields and request.match_rules is not None
                else _MISSING
            ),
            response=(
                MockContractMapper.to_domain_mock_response_model(request.response)
                if "response" in set_fields and request.response is not None
                else _MISSING
            ),
            tags=request.tags if "tags" in set_fields else _MISSING,
        )

    @staticmethod
    def from_domain_mock_model(mock: Mock) -> MockResponseItem:
        """Преобразует доменную модель мока в RESPONSE DTO ответа."""
        return MockResponseItem(
            id=mock.id or "",
            name=mock.name,
            description=mock.description,
            path=mock.path,
            method=mock.method,
            priority=mock.priority,
            active=mock.active,
            scope=mock.scope,
            match_rules=[
                MockContractMapper.from_domain_match_rule_model(rule)
                for rule in mock.match_rules
            ],
            response=MockContractMapper.from_domain_mock_response_model(mock.response),
            tags=mock.tags,
            created_at=mock.created_at,
            updated_at=mock.updated_at,
        )

    @staticmethod
    def to_domain_match_rule_model(rule: MatchRuleItem) -> MatchRule:
        """Преобразует REQUEST DTO правила сопоставления в доменную модель."""
        return MatchRule(
            source=rule.source,
            key=rule.key,
            operator=rule.operator,
            expected=rule.expected,
        )

    @staticmethod
    def to_domain_mock_response_model(response: MockResponseItemDTO) -> MockResponse:
        """Преобразует REQUEST DTO ответа мока в доменную модель."""
        return MockResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
        )

    @staticmethod
    def from_domain_match_rule_model(rule: MatchRule) -> MatchRuleItem:
        """Преобразует доменное правило сопоставления в RESPONSE DTO ответа."""
        return MatchRuleItem(
            source=rule.source,
            key=rule.key,
            operator=rule.operator,
            expected=rule.expected,
        )

    @staticmethod
    def from_domain_mock_response_model(response: MockResponse) -> MockResponseItemDTO:
        """Преобразует доменный ответ мока в RESPONSE DTO ответа."""
        return MockResponseItemDTO(
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
        )
