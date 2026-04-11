
from dataclasses import dataclass, field

from app.domain.models.enums import HttpMethod
from app.domain.models.mocks.match_rule import MatchRule
from app.domain.models.mocks.mock_response import MockResponse

_MISSING = object()


@dataclass(slots=True, frozen=True)
class MockUpdate:
    """Описывает частичное обновление мока.

    Поля со значением ``_MISSING`` считаются не переданными и не применяются.
    """

    name: str | object = field(default=_MISSING)
    description: str | None | object = field(default=_MISSING)
    path: str | object = field(default=_MISSING)
    method: HttpMethod | object = field(default=_MISSING)
    priority: int | object = field(default=_MISSING)
    active: bool | object = field(default=_MISSING)
    scope: str | object = field(default=_MISSING)
    match_rules: list[MatchRule] | object = field(default=_MISSING)
    response: MockResponse | object = field(default=_MISSING)
    tags: list[str] | object = field(default=_MISSING)

    def to_patch_dict(self) -> dict[str, object]:
        """Возвращает словарь только с явно переданными полями."""
        return {
            f: getattr(self, f)
            for f in self.__dataclass_fields__
            if getattr(self, f) is not _MISSING
        }
