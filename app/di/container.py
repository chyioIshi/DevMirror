"""Dependency container for app services and infrastructure adapters."""

from typing import Final, cast

import httpx
from fastapi import Request

from app.application.mocks import MockManagementService, MockResolverService
from app.application.request_logs import RequestLogService
from app.application.side_effects import (
    SideEffectDispatcherService,
    SideEffectExecutionService,
    SideEffectProviderRegistry,
)
from app.config import AppSettings
from app.domain.mocks import MockRepository
from app.domain.mocks.policies import (
    ChainedScopeResolver,
    MockActivationPolicy,
    MockSelectionPolicy,
)
from app.domain.mocks.ports import (
    AsyncTaskScheduler,
    ScopeResolutionStrategy,
    ScopeResolver,
)
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
from app.infra.side_effects import ConnectionRegistry, SideEffectProviderPluginLoader
from app.infra.side_effects.providers import (
    AsyncKafkaSideEffectExecutor,
    AsyncMongoSideEffectExecutor,
    AsyncPostgresSideEffectExecutor,
    AsyncRedisSideEffectExecutor,
    HttpCallbackSideEffectProvider,
    KafkaSideEffectProvider,
    MongoSideEffectProvider,
    PostgresSideEffectProvider,
    RedisSideEffectProvider,
)
from app.infra.tasks import InProcessAsyncTaskScheduler


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
        self._connection_registry: ConnectionRegistry | None = None
        self._http_callback_client: httpx.AsyncClient | None = None
        self._http_callback_side_effect_provider: HttpCallbackSideEffectProvider | None = None
        self._kafka_side_effect_executor: AsyncKafkaSideEffectExecutor | None = None
        self._kafka_side_effect_provider: KafkaSideEffectProvider | None = None
        self._mongo_side_effect_executor: AsyncMongoSideEffectExecutor | None = None
        self._mongo_side_effect_provider: MongoSideEffectProvider | None = None
        self._postgres_side_effect_executor: AsyncPostgresSideEffectExecutor | None = None
        self._postgres_side_effect_provider: PostgresSideEffectProvider | None = None
        self._redis_side_effect_executor: AsyncRedisSideEffectExecutor | None = None
        self._redis_side_effect_provider: RedisSideEffectProvider | None = None
        self._side_effect_provider_registry: SideEffectProviderRegistry | None = None
        self._side_effect_dispatcher_service: SideEffectDispatcherService | None = None
        self._async_task_scheduler: AsyncTaskScheduler | None = None
        self._side_effect_execution_service: SideEffectExecutionService | None = None

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

    @property
    def connection_registry(self) -> ConnectionRegistry:
        """Return the infrastructure connection registry used by plugins."""
        if self._connection_registry is None:
            self._connection_registry = ConnectionRegistry(
                connections=self.settings.side_effect_connections,
            )
        return self._connection_registry

    @property
    def side_effect_provider_registry(self) -> SideEffectProviderRegistry:
        """Return the registry used to resolve side effect providers."""
        if self._side_effect_provider_registry is None:
            registry = SideEffectProviderRegistry()
            if self._http_callback_side_effect_provider is None:
                if self._http_callback_client is None:
                    self._http_callback_client = httpx.AsyncClient()
                self._http_callback_side_effect_provider = HttpCallbackSideEffectProvider(
                    connection_registry=self.connection_registry,
                    client=self._http_callback_client,
                )
            registry.register(self._http_callback_side_effect_provider)
            if self._kafka_side_effect_provider is None:
                if self._kafka_side_effect_executor is None:
                    self._kafka_side_effect_executor = AsyncKafkaSideEffectExecutor()
                self._kafka_side_effect_provider = KafkaSideEffectProvider(
                    connection_registry=self.connection_registry,
                    side_effect_executor=self._kafka_side_effect_executor,
                )
            registry.register(self._kafka_side_effect_provider)
            if self._mongo_side_effect_provider is None:
                if self._mongo_side_effect_executor is None:
                    self._mongo_side_effect_executor = AsyncMongoSideEffectExecutor()
                self._mongo_side_effect_provider = MongoSideEffectProvider(
                    connection_registry=self.connection_registry,
                    side_effect_executor=self._mongo_side_effect_executor,
                )
            registry.register(self._mongo_side_effect_provider)
            if self._postgres_side_effect_provider is None:
                if self._postgres_side_effect_executor is None:
                    self._postgres_side_effect_executor = AsyncPostgresSideEffectExecutor()
                self._postgres_side_effect_provider = PostgresSideEffectProvider(
                    connection_registry=self.connection_registry,
                    side_effect_executor=self._postgres_side_effect_executor,
                )
            registry.register(self._postgres_side_effect_provider)
            if self._redis_side_effect_provider is None:
                if self._redis_side_effect_executor is None:
                    self._redis_side_effect_executor = AsyncRedisSideEffectExecutor()
                self._redis_side_effect_provider = RedisSideEffectProvider(
                    connection_registry=self.connection_registry,
                    side_effect_executor=self._redis_side_effect_executor,
                )
            registry.register(self._redis_side_effect_provider)
            SideEffectProviderPluginLoader(
                connection_registry=self.connection_registry,
            ).load_into(registry)
            self._side_effect_provider_registry = registry
        return self._side_effect_provider_registry

    async def aclose(self) -> None:
        """Close infrastructure resources owned by the container."""
        if self._http_callback_client is not None and not self._http_callback_client.is_closed:
            await self._http_callback_client.aclose()
        if self._kafka_side_effect_executor is not None:
            await self._kafka_side_effect_executor.aclose()
        if self._mongo_side_effect_executor is not None:
            await self._mongo_side_effect_executor.aclose()
        if self._postgres_side_effect_executor is not None:
            await self._postgres_side_effect_executor.aclose()
        if self._redis_side_effect_executor is not None:
            await self._redis_side_effect_executor.aclose()

    @property
    def side_effect_dispatcher_service(self) -> SideEffectDispatcherService:
        """Return the app service that dispatches side effects."""
        if self._side_effect_dispatcher_service is None:
            self._side_effect_dispatcher_service = SideEffectDispatcherService(
                registry=self.side_effect_provider_registry,
            )
        return self._side_effect_dispatcher_service

    @property
    def async_task_scheduler(self) -> AsyncTaskScheduler:
        """Return the adapter used to schedule background async tasks."""
        if self._async_task_scheduler is None:
            self._async_task_scheduler = InProcessAsyncTaskScheduler()
        return self._async_task_scheduler

    @property
    def side_effect_execution_service(self) -> SideEffectExecutionService:
        """Return the app service that executes response side effects."""
        if self._side_effect_execution_service is None:
            self._side_effect_execution_service = SideEffectExecutionService(
                dispatcher_service=self.side_effect_dispatcher_service,
                async_task_scheduler=self.async_task_scheduler,
            )
        return self._side_effect_execution_service


def get_container(request: Request) -> AppContainer:
    """Return the app container stored in FastAPI app state.

    Args:
        request: Incoming FastAPI request.

    Returns:
        App dependency container.
    """
    return cast(AppContainer, request.app.state.container)
