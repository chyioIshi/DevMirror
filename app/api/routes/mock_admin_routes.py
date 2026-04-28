
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status

from app.api.contracts.common.pagination_request import PaginationRequest
from app.api.contracts.mocks.requests import CreateMockRequest, UpdateMockRequest
from app.api.contracts.mocks.responses import MockListResponse, MockResponseItem
from app.application.exceptions import MockNotFoundError
from app.application.mappers.mock_contract_mapper import MockContractMapper
from app.application.services.mock_management_service import MockManagementService
from app.di import get_mock_management_service
from app.domain.mocks.models.mock_list_filters import MockListFilters
from app.domain.shared.enums import HttpMethod

mock_admin_router = APIRouter(tags=["mock-admin"])


@mock_admin_router.post("", response_model=MockResponseItem, status_code=status.HTTP_201_CREATED)
async def create_mock(
    request: CreateMockRequest,
    mock_managment_service: MockManagementService = Depends(get_mock_management_service),
) -> MockResponseItem:
    """Создает новый мок на основе данных из запроса."""
    created_mock = await mock_managment_service.create_mock(
        MockContractMapper.to_domain_mock_model(request)
    )
    return MockContractMapper.from_domain_mock_model(created_mock)


@mock_admin_router.get("/{mock_id}", response_model=MockResponseItem)
async def get_mock(
    mock_id: str,
    mock_managment_service: MockManagementService = Depends(get_mock_management_service),
) -> MockResponseItem:
    """Возвращает мок по id или 404, если он не найден."""
    try:
        finded_mock = await mock_managment_service.get_mock(mock_id)
    except MockNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MockContractMapper.from_domain_mock_model(finded_mock)


@mock_admin_router.get("", response_model=MockListResponse)
async def list_mocks(
    path: str | None = Query(default=None),
    method: HttpMethod | None = Query(default=None),
    active: bool | None = Query(default=None),
    scope: str | None = Query(default=None),
    pagination: PaginationRequest = Body(default=PaginationRequest()),
    mock_managment_service: MockManagementService = Depends(get_mock_management_service),
) -> MockListResponse:
    """Возвращает список моков, подходящих под заданные фильтры,
    с учетом пагинации."""
    items = await mock_managment_service.list_mocks(
        MockListFilters(path=path, method=method, active=active, scope=scope),
        limit=pagination.limit,
        offset=pagination.offset,
    )
    mock_response_items = [MockContractMapper.from_domain_mock_model(item) for item in items]
    return MockListResponse(items=mock_response_items, total=len(mock_response_items))


@mock_admin_router.put("/{mock_id}", response_model=MockResponseItem)
async def update_mock(
    mock_id: str,
    request: UpdateMockRequest,
    mock_managment_service: MockManagementService = Depends(get_mock_management_service),
) -> MockResponseItem:
    """Применяет частичное обновление к существующему моку
    или возвращает 404, если он не найден."""
    try:
        updated_mock = await mock_managment_service.update_mock(
            MockContractMapper.to_update_mock_command(mock_id, request),
        )
    except MockNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MockContractMapper.from_domain_mock_model(updated_mock)


@mock_admin_router.delete("/{mock_id}", status_code=status.HTTP_200_OK)
async def delete_mock(
    mock_id: str,
    mock_managment_service: MockManagementService = Depends(get_mock_management_service),
) -> Response:
    """Удаляет мок по id или возвращает 404, если он не найден."""
    try:
        await mock_managment_service.delete_mock(mock_id)
    except MockNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_200_OK)


@mock_admin_router.post("/{mock_id}/activate", response_model=MockResponseItem)
async def activate_mock(
    mock_id: str,
    deactivate_conflicting: bool = Query(default=False),
    mock_managment_service: MockManagementService = Depends(get_mock_management_service),
) -> MockResponseItem:
    """Активирует мок по id, при необходимости деактивируя конфликтующие моки,
    или возвращает 404, если он не найден."""
    try:
        activated_mock = await mock_managment_service.activate_mock(
            mock_id,
            deactivate_conflicting=deactivate_conflicting,
        )
    except MockNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MockContractMapper.from_domain_mock_model(activated_mock)


@mock_admin_router.post("/{mock_id}/deactivate", response_model=MockResponseItem)
async def deactivate_mock(
    mock_id: str,
    mock_managment_service: MockManagementService = Depends(get_mock_management_service),
) -> MockResponseItem:
    """Деактивирует мок по id или возвращает 404, если он не найден."""
    try:
        deactivated_mock = await mock_managment_service.deactivate_mock(mock_id)
    except MockNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MockContractMapper.from_domain_mock_model(deactivated_mock)
