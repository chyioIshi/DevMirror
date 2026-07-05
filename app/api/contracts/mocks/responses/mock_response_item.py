"""Mock representation contract for API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.contracts.mocks.items import (
    MatchRuleItem,
)
from app.api.contracts.mocks.items import (
    MockResponsePayloadItem as MockResponsePayloadItem,
)
from app.domain.shared import HttpMethod


class MockResponseItem(BaseModel):
    """Response model representing one persisted mock."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(examples=["69d17fb0fa28a0c108a689eb"])
    name: str = Field(examples=["hello-mock"])
    description: str | None = Field(
        default=None,
        examples=["Простой мок для GET /hello"],
    )
    path: str = Field(examples=["/hello"])
    method: HttpMethod = Field(examples=["GET"])
    priority: int = Field(examples=[100])
    active: bool = Field(examples=[True])
    scope: str = Field(examples=["global"])
    mock_session_id: str | None = Field(default=None, examples=["test-run-123"])
    match_rules: list[MatchRuleItem] = Field(
        examples=[
            [
                {
                    "source": "header",
                    "key": "x-test-user",
                    "operator": "eq",
                    "expected": "user123",
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
    tags: list[str] = Field(examples=[["test", "hello"]])
    created_at: datetime = Field(examples=["2000-03-25T21:20:00Z"])
    updated_at: datetime = Field(examples=["2000-03-25T21:20:00Z"])
