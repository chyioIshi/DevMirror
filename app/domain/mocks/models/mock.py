from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Self

from app.domain.mocks.exceptions import MockInvariantError
from app.domain.mocks.models.match_rule import MatchRule
from app.domain.mocks.models.mock_response import MockResponse
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
        """Переименовывает мок."""
        candidate = self._build_candidate(name=name)
        self.name = candidate.name
        self._touch()

    def set_description(self, description: str | None) -> None:
        """Устанавливает описание мока."""
        candidate = self._build_candidate(description=description)
        self.description = candidate.description
        self._touch()

    def change_route(self, *, path: str, method: HttpMethod) -> None:
        """Меняет маршрут мока. Метод и путь не могут быть пустыми."""
        candidate = self._build_candidate(path=path, method=method)
        self.path = candidate.path
        self.method = candidate.method
        self._touch()

    def change_scope(self, scope: str) -> None:
        """Меняет область видимости мока. Не может быть пустой."""
        candidate = self._build_candidate(scope=scope)
        self.scope = candidate.scope
        self._touch()

    def change_priority(self, priority: int) -> None:
        """Меняет приоритет мока. Не может быть отрицательным."""
        candidate = self._build_candidate(priority=priority)
        self.priority = candidate.priority
        self._touch()

    def set_tags(self, tags: list[str]) -> None:
        """Заменяет теги мока."""
        candidate = self._build_candidate(tags=list(tags))
        self.tags = candidate.tags
        self._touch()

    def replace_response(self, response: MockResponse) -> None:
        """Заменяет HTTP-ответ мока."""
        candidate = self._build_candidate(response=response)
        self.response = candidate.response
        self._touch()

    def replace_match_rules(self, match_rules: list[MatchRule]) -> None:
        """Заменяет правила совпадения мока."""
        candidate = self._build_candidate(match_rules=list(match_rules))
        self.match_rules = candidate.match_rules
        self._touch()

    def activate(self) -> None:
        """Активирует мок."""
        if self.active:
            return
        candidate = self._build_candidate(active=True)
        self.active = candidate.active
        self._touch()

    def deactivate(self) -> None:
        """Деактивирует мок."""
        if not self.active:
            return
        candidate = self._build_candidate(active=False)
        self.active = candidate.active
        self._touch()

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
        """Проверяет инварианты мока и выбрасывает исключение, если они нарушены."""
        if not self.name or not self.name.strip():
            raise MockInvariantError("Mock name must not be empty")
        if not self.path or not self.path.strip():
            raise MockInvariantError("Mock path must not be empty")
        if self.priority < 0:
            raise MockInvariantError("Mock priority must be non-negative")
        if not self.scope or not self.scope.strip():
            raise MockInvariantError("Mock scope must not be empty")

    def _build_candidate(self, **changes: object) -> Self:
        """Строит и валидирует кандидатное состояние, не меняя текущий агрегат."""
        return replace(self, **changes)

    def _touch(self) -> None:
        """Обновляет updated_at на текущее время."""
        self.updated_at = datetime.now(tz=UTC)
