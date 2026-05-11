from typing import Final, cast

from fastapi import Request

from app.application.services import (
    MockManagementService,
    MockResolverService,
    RequestLogService,
)
from app.config import Settings
from app.domain.mocks import MockRepository
from app.domain.mocks.policies import (
    ChainedScopeResolver,
    MockActivationPolicy,
    MockSelectionPolicy,
)
from app.domain.mocks.services import (
    MockConflictService,
    MockResolutionService,
    RuleMatcherService,
)
from app.domain.request_logs import RequestLogRepository
from app.domain.shared.ports import (
    ScopeResolutionStrategy,
    ScopeResolver,
)
from app.infra.context import RequestContextResolver
from app.infra.repositories import (
    MongoMockRepository,
    MongoRequestLogRepository,
)
from app.infra.request import RequestDataReader
from app.infra.response import MockResponseBuilder
from app.infra.scope_resolution import (
    DefaultScopeResolutionStrategy,
    HeaderScopeResolutionStrategy,
    JsonBodyFieldScopeResolutionStrategy,
)


class AppContainer:
    """DI-контейнер приложения."""

    def __init__(self, settings: Settings) -> None:
        self.settings: Final[Settings] = settings
        self._request_data_reader: RequestDataReader | None = None
        self._request_context_resolver: RequestContextResolver | None = None
        self._rule_matcher: RuleMatcherService | None = None
        self._scope_resolver: ScopeResolver | None = None
        self._mock_repository: MockRepository | None = None
        self._mock_conflict_service: MockConflictService | None = None
        self._mock_resolution_service: MockResolutionService | None = None
        self._mock_activation_policy: MockActivationPolicy | None = None
        self._request_log_repository: RequestLogRepository | None = None
        self._request_log_service: RequestLogService | None = None
        self._mock_management_service: MockManagementService | None = None
        self._mock_selection_policy: MockSelectionPolicy | None = None
        self._mock_resolver_service: MockResolverService | None = None
        self._mock_response_builder: MockResponseBuilder | None = None

    @property
    def request_data_reader(self) -> RequestDataReader:
        if self._request_data_reader is None:
            self._request_data_reader = RequestDataReader()
        return self._request_data_reader

    @property
    def request_context_resolver(self) -> RequestContextResolver:
        if self._request_context_resolver is None:
            self._request_context_resolver = RequestContextResolver(
                request_data_accessor=self.request_data_reader,
            )
        return self._request_context_resolver

    @property
    def rule_matcher(self) -> RuleMatcherService:
        if self._rule_matcher is None:
            self._rule_matcher = RuleMatcherService()
        return self._rule_matcher

    @property
    def scope_resolver(self) -> ScopeResolver:
        if self._scope_resolver is None:
            strategies: list[ScopeResolutionStrategy] = [
                HeaderScopeResolutionStrategy(self.settings.scope_header_name),
                JsonBodyFieldScopeResolutionStrategy(
                    field_name=self.settings.scope_body_field_name,
                ),
                DefaultScopeResolutionStrategy(self.settings.default_scope),
            ]
            self._scope_resolver = ChainedScopeResolver(strategies=strategies)
        return self._scope_resolver

    @property
    def mock_repository(self) -> MockRepository:
        if self._mock_repository is None:
            self._mock_repository = MongoMockRepository()
        return self._mock_repository

    @property
    def mock_conflict_service(self) -> MockConflictService:
        if self._mock_conflict_service is None:
            self._mock_conflict_service = MockConflictService()
        return self._mock_conflict_service

    @property
    def mock_resolution_service(self) -> MockResolutionService:
        if self._mock_resolution_service is None:
            self._mock_resolution_service = MockResolutionService(
                rule_matcher=self.rule_matcher,
                selection_policy=self.mock_selection_policy,
            )
        return self._mock_resolution_service

    @property
    def mock_activation_policy(self) -> MockActivationPolicy:
        if self._mock_activation_policy is None:
            self._mock_activation_policy = MockActivationPolicy()
        return self._mock_activation_policy

    @property
    def request_log_repository(self) -> RequestLogRepository:
        if self._request_log_repository is None:
            self._request_log_repository = MongoRequestLogRepository()
        return self._request_log_repository

    @property
    def request_log_service(self) -> RequestLogService:
        if self._request_log_service is None:
            self._request_log_service = RequestLogService(
                request_log_repository=self.request_log_repository,
            )
        return self._request_log_service

    @property
    def mock_management_service(self) -> MockManagementService:
        if self._mock_management_service is None:
            self._mock_management_service = MockManagementService(
                repository=self.mock_repository,
                conflict_service=self.mock_conflict_service,
                activation_policy=self.mock_activation_policy,
            )
        return self._mock_management_service

    @property
    def mock_selection_policy(self) -> MockSelectionPolicy:
        if self._mock_selection_policy is None:
            self._mock_selection_policy = MockSelectionPolicy()
        return self._mock_selection_policy

    @property
    def mock_resolver_service(self) -> MockResolverService:
        if self._mock_resolver_service is None:
            self._mock_resolver_service = MockResolverService(
                mock_repository=self.mock_repository,
                request_log_service=self.request_log_service,
                scope_resolver=self.scope_resolver,
                mock_resolution_service=self.mock_resolution_service,
                default_scope=self.settings.default_scope,
            )
        return self._mock_resolver_service

    @property
    def mock_response_builder(self) -> MockResponseBuilder:
        if self._mock_response_builder is None:
            self._mock_response_builder = MockResponseBuilder()
        return self._mock_response_builder


def get_container(request: Request) -> AppContainer:
    """Возвращает контейнер приложения, сохранённый в state app FastAPI."""
    return cast(AppContainer, request.app.state.container)
