from app.api.contracts.mocks import CreateMockRequest, MockResponseItem, UpdateMockRequest
from app.api.contracts.mocks.items import MatchRuleItem
from app.api.contracts.mocks.items import MockResponsePayloadItem as MockResponseItemDTO
from app.application.commands import UNSET, UpdateMockCommand
from app.domain.mocks.models import MatchRule, Mock, MockResponse


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
            active=False,
            scope=request.scope,
            match_rules=[
                MockContractMapper.to_domain_match_rule_model(rule)
                for rule in request.match_rules
            ],
            response=MockContractMapper.to_domain_mock_response_model(request.response),
            tags=request.tags,
        )

    @staticmethod
    def to_update_mock_command(mock_id: str, request: UpdateMockRequest) -> UpdateMockCommand:
        """Преобразует REQUEST DTO частичного обновления в модель UpdateMockCommand."""
        set_fields = request.model_fields_set
        return UpdateMockCommand(
            mock_id=mock_id,
            name=request.name if "name" in set_fields else UNSET,
            description=request.description if "description" in set_fields else UNSET,
            path=request.path if "path" in set_fields else UNSET,
            method=request.method if "method" in set_fields else UNSET,
            priority=request.priority if "priority" in set_fields else UNSET,
            active=request.active if "active" in set_fields else UNSET,
            scope=request.scope if "scope" in set_fields else UNSET,
            match_rules=(
                [MockContractMapper.to_domain_match_rule_model(r) for r in request.match_rules]
                if "match_rules" in set_fields and request.match_rules is not None
                else UNSET
            ),
            response=(
                MockContractMapper.to_domain_mock_response_model(request.response)
                if "response" in set_fields and request.response is not None
                else UNSET
            ),
            tags=request.tags if "tags" in set_fields else UNSET,
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
