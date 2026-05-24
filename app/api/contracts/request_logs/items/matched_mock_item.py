"""Контракт объекта c информацией о моке, зарезолвленным для запроса."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.shared import HttpMethod


class MatchedMockItem(BaseModel):
    """Модель ответа с данными мока, совпавшего с запросом."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(examples=["69d17fb0fa28a0c108a689eb"])
    name: str = Field(examples=["hello-mock"])
    path: str = Field(examples=["/hello"])
    method: HttpMethod = Field(examples=["GET"])
    scope: str = Field(examples=["global"])
    response_status_code: int = Field(examples=[200])
    response_body: Any | None = Field(
        default=None,
        examples=[{"message": "hello from mock"}],
    )
