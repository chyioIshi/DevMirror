
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.shared.enums import MatchOperator, MatchSource


class MatchRule(BaseModel):
    """Описывает одно условие, которому должен соответствовать запрос."""
    model_config = ConfigDict(extra="forbid")

    source: MatchSource
    key: str = Field(default="")
    operator: MatchOperator
    expected: Any | None = None

    @model_validator(mode="after")
    def validate_rule(self) -> Self:
        """Проверяет корректность правила после создания модели."""
        if self.source in {MatchSource.HEADER, MatchSource.QUERY, MatchSource.BODY_JSON} and not self.key:
            raise ValueError(f"`key` is required for source `{self.source}`")

        if self.expected is None:
            raise ValueError("`expected` is required for the selected operator")

        if self.operator == MatchOperator.IN and not isinstance(self.expected, list):
            raise ValueError("`expected` must be a list for operator `in`")

        if self.operator == MatchOperator.EXISTS:
            return self

        return self
