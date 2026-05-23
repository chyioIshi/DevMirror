import logging

from app.infra.logging.context import get_correlation_id, get_request_id


class RequestContextFilter(logging.Filter):
    """Фильтр для добавления request_id и correlation_id в лог-записи.
    Работает как хук для logging, который при каждом логировании добавляет
    в запись текущие значения request_id и correlation_id из контекста.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.correlation_id = get_correlation_id()
        return True
