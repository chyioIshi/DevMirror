"""Mapper between mock API contracts and domain models."""

from app.api.contracts.mocks import (
    CreateMockRequest,
    MockResponseItem,
    UpdateMockRequest,
)
from app.api.contracts.mocks.items import MatchRuleItem, SideEffectItem
from app.api.contracts.mocks.items import MockResponsePayloadItem as MockResponseItemDTO
from app.application.mocks.commands import UNSET, UpdateMockCommand
from app.domain.mocks.models import MatchRule, Mock, MockResponse, SideEffect


class MockContractMapper:
    """Converts mock DTOs to domain models and back."""

    @staticmethod
    def to_domain_mock_model(request: CreateMockRequest) -> Mock:
        """Converts a create mock request DTO to the `Mock` domain model.

        Args:
            request: API request DTO with mock creation data.

        Returns:
            Domain mock model.
        """
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
                for rule in request.match_rules  # noqa: E501
            ],
            response=MockContractMapper.to_domain_mock_response_model(request.response),
            tags=request.tags,
        )

    @staticmethod
    def to_update_mock_command(mock_id: str, request: UpdateMockRequest) -> UpdateMockCommand:  # noqa: E501
        """Converts a partial update request DTO to `UpdateMockCommand`.

        Args:
            mock_id: Identifier of the mock being updated.
            request: API request DTO with partial update data.

        Returns:
            Application command for updating the mock.
        """
        set_fields = request.model_fields_set
        return UpdateMockCommand(
            mock_id=mock_id,
            name=request.name if "name" in set_fields and request.name is not None else UNSET,  # noqa: E501
            description=request.description if "description" in set_fields else UNSET,
            path=request.path if "path" in set_fields and request.path is not None else UNSET,  # noqa: E501
            method=request.method
            if "method" in set_fields and request.method is not None
            else UNSET,
            priority=(
                request.priority
                if "priority" in set_fields and request.priority is not None
                else UNSET
            ),
            scope=request.scope if "scope" in set_fields and request.scope is not None else UNSET,  # noqa: E501
            match_rules=(
                [MockContractMapper.to_domain_match_rule_model(r) for r in request.match_rules]  # noqa: E501
                if "match_rules" in set_fields and request.match_rules is not None
                else UNSET
            ),
            response=(
                MockContractMapper.to_domain_mock_response_model(request.response)
                if "response" in set_fields and request.response is not None
                else UNSET
            ),
            tags=request.tags if "tags" in set_fields and request.tags is not None else UNSET,  # noqa: E501
        )

    @staticmethod
    def from_domain_mock_model(mock: Mock) -> MockResponseItem:
        """Converts a mock domain model to a response DTO.

        Args:
            mock: Domain mock model.

        Returns:
            API response DTO for the mock.
        """
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
                for rule in mock.match_rules  # noqa: E501
            ],
            response=MockContractMapper.from_domain_mock_response_model(mock.response),
            tags=mock.tags,
            created_at=mock.created_at,
            updated_at=mock.updated_at,
        )

    @staticmethod
    def to_domain_match_rule_model(rule: MatchRuleItem) -> MatchRule:
        """Converts a matching rule request DTO to a domain model.

        Args:
            rule: API DTO describing a match rule.

        Returns:
            Domain match rule model.
        """
        return MatchRule(
            source=rule.source,
            key=rule.key,
            operator=rule.operator,
            expected=rule.expected,
        )

    @staticmethod
    def to_domain_mock_response_model(response: MockResponseItemDTO) -> MockResponse:
        """Converts a mock response request DTO to a domain model.

        Args:
            response: API DTO describing a mock HTTP response.

        Returns:
            Domain mock response model.
        """
        return MockResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
            side_effects=[
                MockContractMapper.to_domain_side_effect_model(side_effect)
                for side_effect in response.side_effects
            ],
        )

    @staticmethod
    def to_domain_side_effect_model(side_effect: SideEffectItem) -> SideEffect:
        """Converts a side effect request DTO to a domain model."""
        return SideEffect(
            type=side_effect.type,
            provider=side_effect.provider,
            target=side_effect.target,
            payload_template=side_effect.payload_template,
            options=side_effect.options,
            mode=side_effect.mode,
            fail_policy=side_effect.fail_policy,
            enabled=side_effect.enabled,
        )

    @staticmethod
    def from_domain_match_rule_model(rule: MatchRule) -> MatchRuleItem:
        """Converts a domain matching rule to a response DTO.

        Args:
            rule: Domain match rule model.

        Returns:
            API DTO describing the match rule.
        """
        return MatchRuleItem(
            source=rule.source,
            key=rule.key,
            operator=rule.operator,
            expected=rule.expected,
        )

    @staticmethod
    def from_domain_mock_response_model(response: MockResponse) -> MockResponseItemDTO:
        """Converts a domain mock response to a response DTO.

        Args:
            response: Domain mock response model.

        Returns:
            API DTO describing the mock HTTP response.
        """
        return MockResponseItemDTO(
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
            side_effects=[
                MockContractMapper.from_domain_side_effect_model(side_effect)
                for side_effect in response.side_effects
            ],
        )

    @staticmethod
    def from_domain_side_effect_model(side_effect: SideEffect) -> SideEffectItem:
        """Converts a domain side effect to a response DTO."""
        return SideEffectItem(
            type=side_effect.type,
            provider=side_effect.provider,
            target=side_effect.target,
            payload_template=side_effect.payload_template,
            options=side_effect.options,
            mode=side_effect.mode,
            fail_policy=side_effect.fail_policy,
            enabled=side_effect.enabled,
        )
