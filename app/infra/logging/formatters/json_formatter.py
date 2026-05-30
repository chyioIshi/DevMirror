"""JSON logging formatter."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__)


class JsonLogFormatter(logging.Formatter):
    """Formats log records as compact JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats a log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON-encoded log entry.
        """
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        for field in (
            "request_id",
            "correlation_id",
            "method",
            "path",
            "query",
            "status_code",
            "duration_ms",
            "client_ip",
            "user_agent",
            "request_body",
            "response_body",
        ):
            value = getattr(record, field, None)
            if value is not None and value != "":
                payload[field] = value

        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            if exc_type is not None:
                payload["exception_type"] = exc_type.__name__
            if exc_value is not None:
                payload["exception_message"] = str(exc_value)
            payload["stacktrace"] = self.formatException(record.exc_info)
        else:
            exception_type = getattr(record, "exception_type", None)
            exception_message = getattr(record, "exception_message", None)
            if exception_type:
                payload["exception_type"] = str(exception_type)
            if exception_message:
                payload["exception_message"] = str(exception_message)

        for key, value in self._get_log_record_extra_fields(record).items():
            if key not in payload and value is not None and value != "":
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)

    def _get_log_record_extra_fields(self, record: logging.LogRecord) -> dict[str, Any]:
        """Returns custom fields attached to a log record.

        Args:
            record: Log record to inspect.

        Returns:
            Extra fields that are not part of the standard logging record.
        """
        return {
            key: value
            for key, value in record.__dict__.items()
            if key not in _LOG_RECORD_FIELDS
            and key not in {"message", "asctime"}
            and not key.startswith("_")
        }
