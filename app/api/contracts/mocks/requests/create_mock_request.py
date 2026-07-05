"""Request contract for creating a mock."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.contracts.mocks.items import MatchRuleItem, MockResponsePayloadItem
from app.domain.shared import HttpMethod


class CreateMockRequest(BaseModel):
    """Request model for creating a new mock."""

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
    mock_session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        examples=["test-run-123"],
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
        """Validates that the created mock path starts with ``/``.

        Args:
            value: Path value from the request body.

        Returns:
            Validated path value.

        Raises:
            ValueError: If the path does not start with ``/``.
        """
        if not value.startswith("/"):
            raise ValueError("path must start with '/'")
        return value
