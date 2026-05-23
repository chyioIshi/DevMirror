from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.contracts.mocks.items import MatchRuleItem, MockResponsePayloadItem
from app.domain.shared import HttpMethod


class CreateMockRequest(BaseModel):
    """Модель запроса для создания нового мока."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200, examples=["hello-mock"])
    description: str | None = Field(
        default=None,
        max_length=2000,
        examples=["Простой мок для GET /hello"],
    )
    path: str = Field(min_length=1, max_length=1024, examples=["/hello"])
    method: HttpMethod = Field(examples=["GET"])
    priority: int = Field(default=0, examples=[100])
    scope: str = Field(
        default="global",
        min_length=1,
        max_length=200,
        examples=["global"],
    )
    match_rules: list[MatchRuleItem] = Field(
        default_factory=list,
        examples=[
            [
                {
                    "source": "header",
                    "key": "x-test-user",
                    "operator": "eq",
                    "expected": "stan",
                },
            ],
        ],
    )
    response: MockResponsePayloadItem = Field(
        examples=[
            {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": {"message": "hello from mock"},
            },
        ],
    )
    tags: list[str] = Field(default_factory=list, examples=[["test", "hello"]])

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """Проверяет, что путь создаваемого мока начинается с ``/``."""
        if not value.startswith("/"):
            raise ValueError("path must start with '/'")
        return value
