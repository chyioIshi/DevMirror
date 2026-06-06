"""FastAPI dependency providers backed by the App container."""

from typing import Annotated

from fastapi import Depends

from app.application.mocks import MockManagementService, MockResolverService
from app.application.request_logs import RequestLogService
from app.config import AppSettings
from app.di.container import AppContainer, get_container
from app.infra.context import RequestContextResolver
from app.infra.response import MockResponseBuilder

ContainerDep = Annotated[AppContainer, Depends(get_container)]


def get_app_settings(container: ContainerDep) -> AppSettings:
    """Return app settings from the dependency container.

    Args:
        container: App dependency container.

    Returns:
        Runtime app settings.
    """
    return container.settings


def get_mock_management_service(container: ContainerDep) -> MockManagementService:
    """Return the mock management service from the dependency container.

    Args:
        container: App dependency container.

    Returns:
        Mock management app service.
    """
    return container.mock_management_service


def get_mock_resolver_service(container: ContainerDep) -> MockResolverService:
    """Return the mock resolver service from the dependency container.

    Args:
        container: App dependency container.

    Returns:
        Mock resolver app service.
    """
    return container.mock_resolver_service


def get_mock_response_builder(container: ContainerDep) -> MockResponseBuilder:
    """Return the mock response builder from the dependency container.

    Args:
        container: App dependency container.

    Returns:
        Mock response builder adapter.
    """
    return container.mock_response_builder


def get_request_log_service(container: ContainerDep) -> RequestLogService:
    """Return the request log service from the dependency container.

    Args:
        container: App dependency container.

    Returns:
        Request log app service.
    """
    return container.request_log_service


def get_request_context_resolver(container: ContainerDep) -> RequestContextResolver:
    """Return the request context resolver from the dependency container.

    Args:
        container: App dependency container.

    Returns:
        Request context resolver adapter.
    """
    return container.request_context_resolver
