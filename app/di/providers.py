from typing import Annotated

from fastapi import Depends

from app.application.services.mock_management_service import MockManagementService
from app.application.services.mock_resolver_service import MockResolverService
from app.application.services.request_log_service import RequestLogService
from app.config import Settings
from app.di.container import AppContainer, get_container
from app.infra.context.request_context_resolver import RequestContextResolver
from app.infra.response.mock_response_builder import MockResponseBuilder

ContainerDep = Annotated[AppContainer, Depends(get_container)]


def get_app_settings(container: ContainerDep) -> Settings:
    """Возвращает настройки приложения из контейнера."""
    return container.settings


def get_mock_management_service(container: ContainerDep) -> MockManagementService:
    """Возвращает сервис управления моками из контейнера."""
    return container.mock_management_service


def get_mock_resolver_service(container: ContainerDep) -> MockResolverService:
    """Возвращает сервис резолва моков из контейнера."""
    return container.mock_resolver_service


def get_mock_response_builder(container: ContainerDep) -> MockResponseBuilder:
    """Возвращает билдер HTTP-ответов из контейнера."""
    return container.mock_response_builder


def get_request_log_service(container: ContainerDep) -> RequestLogService:
    """Возвращает сервис журнала запросов из контейнера."""
    return container.request_log_service


def get_request_context_resolver(container: ContainerDep) -> RequestContextResolver:
    """Возвращает резолвер контекста запроса (адаптер edge-уровня)."""
    return container.request_context_resolver
