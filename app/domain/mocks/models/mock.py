"""Mock aggregate and its domain behavior."""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any, Self

from app.domain.mocks.exceptions import (
    InvalidMockRouteError,
    InvalidMockStateError,
    InvalidScopeError,
    MockInvariantError,
)
from app.domain.mocks.models.match_rule import MatchRule
from app.domain.mocks.models.mock_response import MockResponse
from app.domain.shared import HttpMethod


@dataclass(slots=True)
class Mock:
    """Aggregate root that describes a mock and encapsulates its behavior and invariants."""

    name: str
    path: str
    method: HttpMethod
    response: MockResponse
    id: str | None = None
    description: str | None = None
    priority: int = 0
    active: bool = False
    scope: str = "global"
    match_rules: list[MatchRule] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def __post_init__(self) -> None:
        """Validates aggregate invariants after object creation."""
        self._ensure_invariants()

    @classmethod
    def create_new(
        cls,
        *,
        name: str,
        path: str,
        method: HttpMethod,
        response: MockResponse,
        description: str | None = None,
        priority: int = 0,
        active: bool = False,
        scope: str = "global",
        match_rules: list[MatchRule] | None = None,
        tags: list[str] | None = None,
    ) -> Self:
        """Creates a new mock with equal `created_at` and `updated_at` values.

        Args:
            name: Mock name.
            path: Mock route path.
            method: Mock route HTTP method.
            response: Mock HTTP response.
            description: Optional mock description.
            priority: Mock priority.
            active: Initial activation state.
            scope: Mock scope.
            match_rules: Optional request matching rules.
            tags: Optional mock tags.

        Returns:
            New mock aggregate.
        """
        now = datetime.now(tz=UTC)
        return cls(
            name=name,
            description=description,
            path=path,
            method=method,
            priority=priority,
            active=active,
            scope=scope,
            match_rules=list(match_rules) if match_rules else [],
            response=response,
            tags=list(tags) if tags else [],
            created_at=now,
            updated_at=now,
        )

    def rename(self, name: str) -> None:
        """Renames the mock.

        Args:
            name: New mock name.
        """
        candidate = self._build_candidate(name=name)
        self.name = candidate.name
        self._touch()

    def set_description(self, description: str | None) -> None:
        """Sets the mock description.

        Args:
            description: New description or ``None``.
        """
        candidate = self._build_candidate(description=description)
        self.description = candidate.description
        self._touch()

    def change_route(self, *, path: str, method: HttpMethod) -> None:
        """Changes the mock route.

        Args:
            path: New route path.
            method: New route HTTP method.
        """
        candidate = self._build_candidate(path=path, method=method)
        self.path = candidate.path
        self.method = candidate.method
        self._touch()

    def change_scope(self, scope: str) -> None:
        """Changes the mock visibility scope.

        Args:
            scope: New non-empty scope.
        """
        candidate = self._build_candidate(scope=scope)
        self.scope = candidate.scope
        self._touch()

    def change_priority(self, priority: int) -> None:
        """Changes the mock priority.

        Args:
            priority: New non-negative priority.
        """
        candidate = self._build_candidate(priority=priority)
        self.priority = candidate.priority
        self._touch()

    def set_tags(self, tags: list[str]) -> None:
        """Replaces mock tags.

        Args:
            tags: New tag list.
        """
        candidate = self._build_candidate(tags=list(tags))
        self.tags = candidate.tags
        self._touch()

    def replace_response(self, response: MockResponse) -> None:
        """Replaces the mock HTTP response.

        Args:
            response: New mock response.
        """
        candidate = self._build_candidate(response=response)
        self.response = candidate.response
        self._touch()

    def replace_match_rules(self, match_rules: list[MatchRule]) -> None:
        """Replaces mock matching rules.

        Args:
            match_rules: New matching rule list.
        """
        candidate = self._build_candidate(match_rules=list(match_rules))
        self.match_rules = candidate.match_rules
        self._touch()

    def activate(self) -> None:
        """Activates the mock."""
        if self.active:
            return
        candidate = self._build_candidate(active=True)
        self.active = candidate.active
        self._touch()

    def deactivate(self) -> None:
        """Deactivates the mock."""
        if not self.active:
            return
        candidate = self._build_candidate(active=False)
        self.active = candidate.active
        self._touch()

    def conflicts_with(self, other: Self) -> bool:
        """Checks whether another mock conflicts with this mock.

        Args:
            other: Mock to compare with the current mock.

        Returns:
            True when route, scope, and match rules conflict; otherwise False.
        """
        return (
            self.id != other.id
            and self.path == other.path
            and self.method == other.method
            and self.scope == other.scope
            and self.match_rules == other.match_rules
        )

    def _ensure_invariants(self) -> None:
        """Validates mock invariants.

        Raises:
            InvalidMockStateError: If the mock name is empty.
            InvalidMockRouteError: If the mock path is empty.
            MockInvariantError: If the priority is negative.
            InvalidScopeError: If the scope is empty.
        """
        if not self.name or not self.name.strip():
            raise InvalidMockStateError("Mock name must not be empty")
        if not self.path or not self.path.strip():
            raise InvalidMockRouteError("Mock path must not be empty")
        if self.priority < 0:
            raise MockInvariantError("Mock priority must be non-negative")
        if not self.scope or not self.scope.strip():
            raise InvalidScopeError("Mock scope must not be empty")

    def _build_candidate(self, **changes: Any) -> Self:
        """Builds and validates a candidate state without mutating the current aggregate.

        Args:
            **changes: Field values to replace in the candidate state.

        Returns:
            Validated mock candidate.
        """
        return replace(self, **changes)

    def _touch(self) -> None:
        """Updates `updated_at` to the current time."""
        self.updated_at = datetime.now(tz=UTC)
