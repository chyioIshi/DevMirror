"""Admin routes for managing mocks."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Response, status

from app.api.contracts.common import PaginationRequest
from app.api.contracts.mocks import (
    CreateMockRequest,
    MockListResponse,
    MockResponseItem,
    UpdateMockRequest,
)
from app.api.mappers import MockContractMapper
from app.application.mocks import MockManagementService
from app.di import get_mock_management_service
from app.domain.mocks.models import MockListFilters
from app.domain.shared import HttpMethod

mock_admin_router = APIRouter(tags=["mock-admin"])
MockManagementServiceDep = Annotated[
    MockManagementService,
    Depends(get_mock_management_service),
]


@mock_admin_router.post("", response_model=MockResponseItem, status_code=status.HTTP_201_CREATED)  # noqa: E501
async def create_mock(
    request: CreateMockRequest,
    mock_managment_service: MockManagementServiceDep,
) -> MockResponseItem:
    """Creates a new mock from request data.

    Args:
        request: API request body with mock data.
        mock_managment_service: Application service for mock management.

    Returns:
        API response DTO for the created mock.
    """
    created_mock = await mock_managment_service.create_mock(
        MockContractMapper.to_domain_mock_model(request)
    )
    return MockContractMapper.from_domain_mock_model(created_mock)


@mock_admin_router.get("/{mock_id}", response_model=MockResponseItem)
async def get_mock(
    mock_id: str,
    mock_managment_service: MockManagementServiceDep,
) -> MockResponseItem:
    """Returns a mock by id or 404 when it is not found.

    Args:
        mock_id: Id of the requested mock.
        mock_managment_service: Application service for mock management.

    Returns:
        API response DTO for the requested mock.
    """
    finded_mock = await mock_managment_service.get_mock(mock_id)
    return MockContractMapper.from_domain_mock_model(finded_mock)


@mock_admin_router.get("", response_model=MockListResponse)
async def list_mocks(
    mock_managment_service: MockManagementServiceDep,
    path: Annotated[str | None, Query()] = None,
    method: Annotated[HttpMethod | None, Query()] = None,
    active: Annotated[bool | None, Query()] = None,
    scope: Annotated[str | None, Query()] = None,
    pagination: Annotated[PaginationRequest | None, Body()] = None,
) -> MockListResponse:
    """Returns mocks matching the provided filters with pagination.

    Args:
        mock_managment_service: Application service for mock management.
        path: Optional path filter.
        method: Optional HTTP method filter.
        active: Optional activation state filter.
        scope: Optional scope filter.
        pagination: Optional pagination request body.

    Returns:
        API response DTO with matching mocks.
    """
    pagination = pagination or PaginationRequest()
    items = await mock_managment_service.list_mocks(
        MockListFilters(path=path, method=method, active=active, scope=scope),
        limit=pagination.limit,
        offset=pagination.offset,
    )
    mock_response_items = [MockContractMapper.from_domain_mock_model(item) for item in items]  # noqa: E501
    return MockListResponse(items=mock_response_items, total=len(mock_response_items))


@mock_admin_router.put("/{mock_id}", response_model=MockResponseItem)
async def update_mock(
    mock_id: str,
    request: UpdateMockRequest,
    mock_managment_service: MockManagementServiceDep,
) -> MockResponseItem:
    """Applies a partial update to an existing mock or returns 404 when it is not found.

    Args:
        mock_id: Id of the mock being updated.
        request: API request body with partial update data.
        mock_managment_service: Application service for mock management.

    Returns:
        API response DTO for the updated mock.
    """
    updated_mock = await mock_managment_service.update_mock(
        MockContractMapper.to_update_mock_command(mock_id, request),
    )
    return MockContractMapper.from_domain_mock_model(updated_mock)


@mock_admin_router.delete("/{mock_id}", status_code=status.HTTP_200_OK)
async def delete_mock(
    mock_id: str,
    mock_managment_service: MockManagementServiceDep,
) -> Response:
    """Deletes a mock by id or returns 404 when it is not found.

    Args:
        mock_id: Id of the mock being deleted.
        mock_managment_service: Application service for mock management.

    Returns:
        Empty HTTP 200 response.
    """
    await mock_managment_service.delete_mock(mock_id)
    return Response(status_code=status.HTTP_200_OK)


@mock_admin_router.post("/{mock_id}/activate", response_model=MockResponseItem)
async def activate_mock(
    mock_id: str,
    mock_managment_service: MockManagementServiceDep,
    deactivate_conflicting: Annotated[bool, Query()] = False,
) -> MockResponseItem:
    """Activates a mock by id, optionally deactivating conflicting mocks.

    Args:
        mock_id: Id of the mock being activated.
        mock_managment_service: Application service for mock management.
        deactivate_conflicting: Whether conflicting mocks should be deactivated.

    Returns:
        API response DTO for the activated mock.
    """
    activated_mock = await mock_managment_service.activate_mock(
        mock_id,
        deactivate_conflicting=deactivate_conflicting,
    )
    return MockContractMapper.from_domain_mock_model(activated_mock)


@mock_admin_router.post("/{mock_id}/deactivate", response_model=MockResponseItem)
async def deactivate_mock(
    mock_id: str,
    mock_managment_service: MockManagementServiceDep,
) -> MockResponseItem:
    """Deactivates a mock by id or returns 404 when it is not found.

    Args:
        mock_id: Id of the mock being deactivated.
        mock_managment_service: Application service for mock management.

    Returns:
        API response DTO for the deactivated mock.
    """
    deactivated_mock = await mock_managment_service.deactivate_mock(mock_id)
    return MockContractMapper.from_domain_mock_model(deactivated_mock)
