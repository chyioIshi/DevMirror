
from pydantic import BaseModel, ConfigDict, Field

from app.api.contracts.request_logs.items.request_log_record_item import (
    RequestLogRecordItem,
)


class RequestLogListResponse(BaseModel):
    """Модель ответа со списком записей журнала."""

    model_config = ConfigDict(extra="forbid")

    items: list[RequestLogRecordItem] = Field(
        examples=[
            [
                {
                    "id": "69d180c649e00527f114ec01",
                    "request_context": {
                        "id": "ef7d9f7588b34dd98fa4b6201fd83d95",
                        "method": "GET",
                        "path": "/hello",
                        "headers": {
                            "user-agent": "bruno-runtime/3.2.0",
                            "host": "localhost:8000",
                        },
                        "query_params": {},
                        "body": None,
                        "timestamp": "2000-03-25T21:21:10Z",
                    },
                    "matched_mock": {
                        "id": "69d17fb0fa28a0c108a689eb",
                        "name": "hello-mock",
                        "path": "/hello",
                        "method": "GET",
                        "scope": "global",
                        "response_status_code": 200,
                        "response_body": {"message": "hello from mock"},
                    },
                    "scope": "global",
                    "response_status_code": 200,
                    "created_at": "2000-03-25T21:21:10Z",
                },
            ],
        ],
    )
    total: int = Field(examples=[1])
