from pydantic import BaseModel, ConfigDict, Field

from app.api.contracts.mocks.responses.mock_response_item import MockResponseItem


class MockListResponse(BaseModel):
    """Модель ответа со списком моков и их количеством."""

    model_config = ConfigDict(extra="forbid")

    items: list[MockResponseItem] = Field(
        examples=[
            [
                {
                    "id": "69d17fb0fa28a0c108a689eb",
                    "name": "hello-mock",
                    "description": "Простой мок для GET /hello",
                    "path": "/hello",
                    "method": "GET",
                    "priority": 100,
                    "active": True,
                    "scope": "global",
                    "match_rules": [],
                    "response": {
                        "status_code": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": {"message": "hello from mock"},
                    },
                    "tags": ["demo", "hello"],
                    "created_at": "2000-03-25T21:20:00Z",
                    "updated_at": "2000-03-25T21:20:00Z",
                },
            ],
        ],
    )
    total: int = Field(examples=[1])
