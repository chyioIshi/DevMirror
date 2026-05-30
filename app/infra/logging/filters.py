"""Logging filters that enrich log records with request context."""

import logging

from app.infra.logging.context import get_correlation_id, get_request_id


class RequestContextFilter(logging.Filter):
    """Adds request id and correlation id to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Adds context fields to a log record.

        Args:
            record: Log record to enrich.

        Returns:
            Always True so the record is not filtered out.
        """
        record.request_id = get_request_id()
        record.correlation_id = get_correlation_id()
        return True
