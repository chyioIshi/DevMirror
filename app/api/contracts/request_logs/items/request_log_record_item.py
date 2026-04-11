
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.contracts.request_logs.items.matched_mock_item import MatchedMockItem
from app.api.contracts.request_logs.items.request_context_item import RequestContextItem


class RequestLogRecordItem(BaseModel):
    """Модель ответа для одной записи журнала запросов."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(examples=["69d180c649e00527f114ec01"])
    request_context: RequestContextItem = Field(
        examples=[
            {
                "id": "ef7d9f7588b34dd98fa4b6201fd83d95",
                "method": "GET",
                "path": "/hello",
                "headers": {
                    "user-agent": "bruno-runtime/3.2.0",
                    "host": "localhost:8000",
                },
                "query_params": {},
                "body": None,
                "timestamp": "2026-04-04T21:21:10Z",
            },
        ],
    )
    matched_mock: MatchedMockItem | None = Field(
        default=None,
        examples=[
            {
                "id": "69d17fb0fa28a0c108a689eb",
                "name": "hello-mock",
                "path": "/hello",
                "method": "GET",
                "scope": "global",
                "response_status_code": 200,
                "response_body": {"message": "hello from mock"},
            },
        ],
    )
    scope: str | None = Field(default=None, examples=["global"])
    response_status_code: int | None = Field(default=None, examples=[200])
    created_at: datetime = Field(examples=["2000-03-25T21:21:10Z"])
