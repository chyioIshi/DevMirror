"""Dependency container for app services and infrastructure adapters."""

from typing import Final, cast

from fastapi import Request

from app.application.mocks import MockManagementService, MockResolverService
from app.application.request_logs import RequestLogService
from app.config import AppSettings
from app.domain.mocks import MockRepository
from app.domain.mocks.policies import (
    ChainedScopeResolver,
    MockActivationPolicy,
    MockSelectionPolicy,
)
from app.domain.mocks.ports import ScopeResolutionStrategy, ScopeResolver
from app.domain.mocks.services import (
    MockConflictService,
    MockResolutionService,
    RuleMatcherService,
)
from app.domain.request_logs import RequestLogRepository
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
    """Builds and stores lazily initialized app dependencies."""

    def __init__(self, settings: AppSettings) -> None:
        """Initialize the container with app settings.

        Args:
            settings: Runtime app settings used to configure dependencies.
        """
        self.settings: Final[AppSettings] = settings
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
        """Return the adapter that reads HTTP request data.

        Returns:
            Request data reader instance.
        """
        if self._request_data_reader is None:
            self._request_data_reader = RequestDataReader()
        return self._request_data_reader

    @property
    def request_context_resolver(self) -> RequestContextResolver:
        """Return the resolver that converts HTTP requests into domain context.

        Returns:
            Request context resolver instance.
        """
        if self._request_context_resolver is None:
            self._request_context_resolver = RequestContextResolver(
                request_data_accessor=self.request_data_reader,
            )
        return self._request_context_resolver

    @property
    def rule_matcher(self) -> RuleMatcherService:
        """Return the service that matches incoming requests against mock rules.

        Returns:
            Rule matcher service instance.
        """
        if self._rule_matcher is None:
            self._rule_matcher = RuleMatcherService()
        return self._rule_matcher

    @property
    def scope_resolver(self) -> ScopeResolver:
        """Return the chained scope resolver configured from settings.

        Returns:
            Scope resolver instance.
        """
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
        """Return the repository used to persist and query mocks.

        Returns:
            Mock repository instance.
        """
        if self._mock_repository is None:
            self._mock_repository = MongoMockRepository()
        return self._mock_repository

    @property
    def mock_conflict_service(self) -> MockConflictService:
        """Return the service that detects conflicts between mock definitions.

        Returns:
            Mock conflict service instance.
        """
        if self._mock_conflict_service is None:
            self._mock_conflict_service = MockConflictService()
        return self._mock_conflict_service

    @property
    def mock_resolution_service(self) -> MockResolutionService:
        """Return the service that selects the matching mock response.

        Returns:
            Mock resolution service instance.
        """
        if self._mock_resolution_service is None:
            self._mock_resolution_service = MockResolutionService(
                rule_matcher=self.rule_matcher,
                selection_policy=self.mock_selection_policy,
            )
        return self._mock_resolution_service

    @property
    def mock_activation_policy(self) -> MockActivationPolicy:
        """Return the policy that controls mock activation conflicts.

        Returns:
            Mock activation policy instance.
        """
        if self._mock_activation_policy is None:
            self._mock_activation_policy = MockActivationPolicy()
        return self._mock_activation_policy

    @property
    def request_log_repository(self) -> RequestLogRepository:
        """Return the repository used to persist request logs.

        Returns:
            Request log repository instance.
        """
        if self._request_log_repository is None:
            self._request_log_repository = MongoRequestLogRepository()
        return self._request_log_repository

    @property
    def request_log_service(self) -> RequestLogService:
        """Return the app service that manages request logs.

        Returns:
            Request log service instance.
        """
        if self._request_log_service is None:
            self._request_log_service = RequestLogService(
                request_log_repository=self.request_log_repository,
            )
        return self._request_log_service

    @property
    def mock_management_service(self) -> MockManagementService:
        """Return the app service that manages mock definitions.

        Returns:
            Mock management service instance.
        """
        if self._mock_management_service is None:
            self._mock_management_service = MockManagementService(
                repository=self.mock_repository,
                conflict_service=self.mock_conflict_service,
                activation_policy=self.mock_activation_policy,
            )
        return self._mock_management_service

    @property
    def mock_selection_policy(self) -> MockSelectionPolicy:
        """Return the policy that orders and selects candidate mocks.

        Returns:
            Mock selection policy instance.
        """
        if self._mock_selection_policy is None:
            self._mock_selection_policy = MockSelectionPolicy()
        return self._mock_selection_policy

    @property
    def mock_resolver_service(self) -> MockResolverService:
        """Return the app service that resolves runtime mock requests.

        Returns:
            Mock resolver service instance.
        """
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
        """Return the adapter that builds FastAPI responses from domain responses.

        Returns:
            Mock response builder instance.
        """
        if self._mock_response_builder is None:
            self._mock_response_builder = MockResponseBuilder()
        return self._mock_response_builder


def get_container(request: Request) -> AppContainer:
    """Return the app container stored in FastAPI app state.

    Args:
        request: Incoming FastAPI request.

    Returns:
        App dependency container.
    """
    return cast(AppContainer, request.app.state.container)
