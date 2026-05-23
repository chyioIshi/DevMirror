from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.shared import HttpMethod


class RequestContextItem(BaseModel):
    """Модель ответа с контекстом входящего запроса."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(examples=["ef7d9f7588b34dd98fa4b6201fd83d95"])
    method: HttpMethod = Field(examples=["GET"])
    path: str = Field(examples=["/hello"])
    headers: dict[str, str] = Field(
        default_factory=dict,
        examples=[
            {
                "user-agent": "bruno-runtime/3.2.0",
                "host": "localhost:8000",
            },
        ],
    )
    query_params: dict[str, Any] = Field(default_factory=dict, examples=[{}])
    body: Any | None = Field(default=None, examples=[None, {"userId": "123"}])
    timestamp: datetime = Field(examples=["2000-03-25T21:21:10Z"])
