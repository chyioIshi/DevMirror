from dataclasses import dataclass, field
from typing import Any

from app.domain.mocks.models.match_rule import MatchRule
from app.domain.mocks.models.mock_response import MockResponse
from app.domain.shared.enums import HttpMethod

_MISSING: Any = object()


@dataclass(slots=True, frozen=True)
class MockUpdate:
    """Описывает частичное обновление мока.

    Поля со значением ``_MISSING`` считаются не переданными и не применяются.
    """

    name: str = field(default=_MISSING)
    description: str | None = field(default=_MISSING)
    path: str = field(default=_MISSING)
    method: HttpMethod = field(default=_MISSING)
    priority: int = field(default=_MISSING)
    active: bool = field(default=_MISSING)
    scope: str = field(default=_MISSING)
    match_rules: list[MatchRule] = field(default=_MISSING)
    response: MockResponse = field(default=_MISSING)
    tags: list[str] = field(default=_MISSING)

    def to_patch_dict(self) -> dict[str, Any]:
        """Возвращает словарь только с явно переданными полями."""
        return {
            f: getattr(self, f)
            for f in self.__dataclass_fields__
            if getattr(self, f) is not _MISSING
        }
