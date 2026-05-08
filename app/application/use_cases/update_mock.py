import logging

from app.application.commands.update_mock_command import UNSET, UpdateMockCommand
from app.application.exceptions import MockNotFoundError, ValidationError
from app.domain.mocks.models.mock import Mock
from app.domain.mocks.repository import MockRepository

logger = logging.getLogger(__name__)


# TODO: временное решение
async def update_mock(cmd: UpdateMockCommand, repo: MockRepository) -> Mock:
    """UseCase обновления мока (вынес в usecase временно, чтобы не раздувать сервис)."""
    if not cmd.has_changes():
        raise ValidationError(
            "Update command must contain at least one field",
            details={"mock_id": cmd.mock_id},
        )

    current_mock = await repo.get_by_id(cmd.mock_id)
    if current_mock is None:
        raise MockNotFoundError(mock_id=cmd.mock_id)

    if cmd.name is not UNSET:
        current_mock.rename(cmd.name)
    if cmd.description is not UNSET:
        current_mock.set_description(cmd.description)

    route_path = current_mock.path
    route_method = current_mock.method
    route_changed = False
    if cmd.path is not UNSET:
        route_path = cmd.path
        route_changed = True
    if cmd.method is not UNSET:
        route_method = cmd.method
        route_changed = True
    if route_changed:
        current_mock.change_route(path=route_path, method=route_method)

    if cmd.scope is not UNSET:
        current_mock.change_scope(cmd.scope)
    if cmd.priority is not UNSET:
        current_mock.change_priority(cmd.priority)
    if cmd.tags is not UNSET:
        current_mock.set_tags(cmd.tags)
    if cmd.response is not UNSET:
        current_mock.replace_response(cmd.response)
    if cmd.match_rules is not UNSET:
        current_mock.replace_match_rules(cmd.match_rules)
    if cmd.active is not UNSET:
        current_mock.activate() if cmd.active else current_mock.deactivate()

    logger.debug(
        f"Применено обновление к моку {current_mock.name} с id={current_mock.id}",
        extra={
            "mock_id": current_mock.id,
            "updated_fields": {
                field: value for field, value in UpdateMockCommand.__dict__.items() if value is not UNSET
            }
        }
     )
    return await repo.save(current_mock)
