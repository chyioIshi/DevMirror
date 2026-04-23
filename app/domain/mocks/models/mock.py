from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from app.domain.mocks.exceptions import MockInvariantError
from app.domain.mocks.models.match_rule import MatchRule
from app.domain.mocks.models.mock_response import MockResponse
from app.domain.mocks.models.mock_update import MockUpdate
from app.domain.shared.enums import HttpMethod


@dataclass(slots=True)
class Mock:
    """Aggregate root: описывает мок и инкапсулирует его поведение
      и инварианты."""

    name: str
    path: str
    method: HttpMethod
    response: MockResponse
    id: str | None = None
    description: str | None = None
    priority: int = 0
    active: bool = True
    scope: str = "global"
    match_rules: list[MatchRule] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def __post_init__(self) -> None:
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
        active: bool = True,
        scope: str = "global",
        match_rules: list[MatchRule] | None = None,
        tags: list[str] | None = None,
    ) -> Self:
        """Фабрика нового мока. created_at == updated_at."""
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
        self.name = name
        self._ensure_invariants()
        self._touch()

    def set_description(self, description: str | None) -> None:
        self.description = description
        self._touch()

    def change_route(self, *, path: str, method: HttpMethod) -> None:
        self.path = path
        self.method = method
        self._ensure_invariants()
        self._touch()

    def change_scope(self, scope: str) -> None:
        self.scope = scope
        self._ensure_invariants()
        self._touch()

    def change_priority(self, priority: int) -> None:
        self.priority = priority
        self._ensure_invariants()
        self._touch()

    def set_tags(self, tags: list[str]) -> None:
        self.tags = list(tags)
        self._touch()

    def replace_response(self, response: MockResponse) -> None:
        self.response = response
        self._touch()

    def replace_match_rules(self, match_rules: list[MatchRule]) -> None:
        self.match_rules = list(match_rules)
        self._touch()

    def activate(self) -> None:
        """Активирует мок. Готовность гарантирована базовыми инвариантами."""
        if self.active:
            return
        self.active = True
        self._touch()

    def deactivate(self) -> None:
        if not self.active:
            return
        self.active = False
        self._touch()

    def apply_update(self, update: MockUpdate) -> None:
        """Применяет частичный апдейт через методы агрегата."""
        patch = update.to_patch_dict()
        if "name" in patch:
            self.rename(patch["name"])
        if "description" in patch:
            self.set_description(patch["description"])
        if "path" in patch or "method" in patch:
            self.change_route(
                path=patch.get("path", self.path),
                method=patch.get("method", self.method),
            )
        if "scope" in patch:
            self.change_scope(patch["scope"])
        if "priority" in patch:
            self.change_priority(patch["priority"])
        if "tags" in patch:
            self.set_tags(patch["tags"])
        if "response" in patch:
            self.replace_response(patch["response"])
        if "match_rules" in patch:
            self.replace_match_rules(patch["match_rules"])
        if "active" in patch:
            self.activate() if patch["active"] else self.deactivate()

    def conflicts_with(self, other: Self) -> bool:
        """Конфликт по сигнатуре маршрута + одинаковым правилам."""
        return (
            self.id != other.id
            and self.path == other.path
            and self.method == other.method
            and self.scope == other.scope
            and self.match_rules == other.match_rules
        )

    def _ensure_invariants(self) -> None:
        if not self.name or not self.name.strip():
            raise MockInvariantError("Mock name must not be empty")
        if not self.path or not self.path.strip():
            raise MockInvariantError("Mock path must not be empty")
        if self.priority < 0:
            raise MockInvariantError("Mock priority must be non-negative")
        if not self.scope or not self.scope.strip():
            raise MockInvariantError("Mock scope must not be empty")

    def _touch(self) -> None:
        self.updated_at = datetime.now(tz=UTC)
