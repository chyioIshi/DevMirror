from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RequestLogVerificationResult:
    """Хранит результат проверки журнала запросов."""

    matched: bool
    actual_count: int
