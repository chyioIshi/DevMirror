"""Side effect model declared by mock responses."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.mocks.exceptions import InvalidSideEffectError


class SideEffectType(StrEnum):
    """Supported side effect kinds."""

    MESSAGE_PUBLISH = "message_publish"
    DB_INSERT = "db_insert"
    DB_UPDATE = "db_update"
    HTTP_CALLBACK = "http_callback"


class SideEffectMode(StrEnum):
    """Execution modes for side effects."""

    SYNC = "sync"
    ASYNC = "async"


class SideEffectFailPolicy(StrEnum):
    """Failure handling policies for side effects."""

    IGNORE = "ignore"
    FAIL_MOCK = "fail_mock"
    RETRY = "retry"


@dataclass(slots=True, frozen=True)
class SideEffect:
    """A side effect declaration attached to a mock response."""

    type: SideEffectType
    provider: str
    target: dict[str, Any]
    payload_template: dict[str, Any]
    options: dict[str, Any] = field(default_factory=dict)
    mode: SideEffectMode = SideEffectMode.ASYNC
    fail_policy: SideEffectFailPolicy = SideEffectFailPolicy.IGNORE
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validates the side effect declaration."""
        if not self.provider.strip():
            raise InvalidSideEffectError("SideEffect provider must be a non-empty string")

        self._validate_target()
        self._validate_fail_policy_options()

    def _validate_target(self) -> None:
        if self.type == SideEffectType.MESSAGE_PUBLISH:
            self._require_any_target_key("topic", "queue", "destination")
            return

        if self.type in {SideEffectType.DB_INSERT, SideEffectType.DB_UPDATE}:
            self._require_any_target_key("table", "collection")
            return

        if self.type == SideEffectType.HTTP_CALLBACK:
            self._require_target_key("connection")

    def _validate_fail_policy_options(self) -> None:
        if self.fail_policy != SideEffectFailPolicy.RETRY:
            return

        max_attempts = self.options.get("max_attempts")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
            raise InvalidSideEffectError(
                "SideEffect retry fail_policy requires options.max_attempts to be a positive integer",
                details={"field": "options.max_attempts"},
            )

    def _require_any_target_key(self, *keys: str) -> None:
        if any(self._has_non_empty_target_value(key) for key in keys):
            return

        raise InvalidSideEffectError(
            f"SideEffect {self.type} target must define one of: {', '.join(keys)}",
            details={"field": "target", "keys": list(keys), "type": self.type},
        )

    def _require_target_key(self, key: str) -> None:
        if self._has_non_empty_target_value(key):
            return

        raise InvalidSideEffectError(
            f"SideEffect {self.type} target must define {key}",
            details={"field": f"target.{key}", "type": self.type},
        )

    def _has_non_empty_target_value(self, key: str) -> bool:
        value = self.target.get(key)
        return isinstance(value, str) and bool(value.strip())
