from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.domain.shared import HttpMethod


@dataclass(slots=True, frozen=True)
class RequestContext:
    """Описывает контекст запроса."""

    method: HttpMethod
    path: str
    id: str = field(default_factory=lambda: uuid4().hex)
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)
    body: Any = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
