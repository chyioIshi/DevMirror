"""Runtime connection registry passed to side effect provider plugins."""

from typing import Any


class ConnectionRegistry:
    """Stores infrastructure connections by name for provider factories."""

    def __init__(self) -> None:
        self._connections: dict[str, Any] = {}

    def register(self, name: str, connection: Any) -> None:
        """Registers a runtime connection by name."""
        self._connections[name] = connection

    def get(self, name: str) -> Any:
        """Returns a registered runtime connection by name."""
        return self._connections[name]
