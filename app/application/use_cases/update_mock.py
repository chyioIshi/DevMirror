"""UseCase для обновления мока.

Модуль содержит временно вынесенную функцию обновления мока, которая
координирует загрузку агрегата, применение изменений и сохранение результата.
"""

import logging
from typing import cast

from app.application.commands import UNSET, UnsetType, UpdateMockCommand
from app.application.exceptions import MockNotFoundError, ValidationError
from app.domain.mocks import MockRepository
from app.domain.mocks.models import Mock

logger = logging.getLogger(__name__)


# TODO: временное решение
async def update_mock(cmd: UpdateMockCommand, repo: MockRepository) -> Mock:
    """Обновляет существующий мок.

    Args:
        cmd: Команда с идентификатором мока и полями, которые нужно изменить.
        repo: Репозиторий моков.

    Returns:
        Обновленный мок после сохранения в репозитории.

    Raises:
        ValidationError: Если команда не содержит ни одного изменяемого поля.
        MockNotFoundError: Если мок с указанным идентификатором не найден.
    """
    if not cmd.has_changes():
        raise ValidationError(
            "Update command must contain at least one field",
            details={"mock_id": cmd.mock_id},
        )

    current_mock = await repo.get_by_id(cmd.mock_id)
    if current_mock is None:
        raise MockNotFoundError(mock_id=cmd.mock_id)

    if cmd.name is not UNSET:
        current_mock.rename(_set_value(cmd.name))
    if cmd.description is not UNSET:
        current_mock.set_description(_set_value(cmd.description))

    route_path = current_mock.path
    route_method = current_mock.method
    route_changed = False
    if cmd.path is not UNSET:
        route_path = _set_value(cmd.path)
        route_changed = True
    if cmd.method is not UNSET:
        route_method = _set_value(cmd.method)
        route_changed = True
    if route_changed:
        current_mock.change_route(path=route_path, method=route_method)

    if cmd.scope is not UNSET:
        current_mock.change_scope(_set_value(cmd.scope))
    if cmd.priority is not UNSET:
        current_mock.change_priority(_set_value(cmd.priority))
    if cmd.tags is not UNSET:
        current_mock.set_tags(_set_value(cmd.tags))
    if cmd.response is not UNSET:
        current_mock.replace_response(_set_value(cmd.response))
    if cmd.match_rules is not UNSET:
        current_mock.replace_match_rules(_set_value(cmd.match_rules))
    logger.debug(
        f"Применено обновление к моку {current_mock.name} с id={current_mock.id}",
        extra={
            "mock_id": current_mock.id,
            "updated_fields": {
                field: value
                for field, value in UpdateMockCommand.__dict__.items()
                if value is not UNSET
            },
        },
    )
    return await repo.save(current_mock)


def _set_value[T](value: T | UnsetType) -> T:
    """Возвращает заданное значение обновляемого поля.

    Args:
        value: Значение поля команды обновления.

    Returns:
        Значение поля без маркера `UNSET`.

    Raises:
        AssertionError: Если helper вызван для поля без заданного значения.
    """
    if value is UNSET:
        raise AssertionError("Update field value is unset")
    return cast(T, value)
