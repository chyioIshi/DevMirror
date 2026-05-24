"""Контракт запроса на частичное обновление мока."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.contracts.mocks.items import MatchRuleItem, MockResponsePayloadItem
from app.domain.shared import HttpMethod


class UpdateMockRequest(BaseModel):
    """Модель запроса для обновления существующего мока."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        examples=["hello-mock-v2"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        examples=["Обновлённое описание мока"],
    )
    path: str | None = Field(
        default=None,
        min_length=1,
        max_length=1024,
        examples=["/hello-updated"],
    )
    method: HttpMethod | None = Field(default=None, examples=["POST"])
    priority: int | None = Field(default=None, examples=[150])
    scope: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        examples=["global"],
    )
    match_rules: list[MatchRuleItem] | None = Field(
        default=None,
        examples=[
            [
                {
                    "source": "query",
                    "key": "mode",
                    "operator": "eq",
                    "expected": "test",
                },
            ],
        ],
    )
    response: MockResponsePayloadItem | None = Field(
        default=None,
        examples=[
            {
                "status_code": 202,
                "headers": {"Content-Type": "application/json"},
                "body": {"message": "mock updated"},
            },
        ],
    )
    tags: list[str] | None = Field(default=None, examples=[["test", "updated"]])

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str | None) -> str | None:
        """Проверяет поле пути, если оно передано в запросе."""
        if value is not None and not value.startswith("/"):
            raise ValueError("path must start with '/'")
        return value
