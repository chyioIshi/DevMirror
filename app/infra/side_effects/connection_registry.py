"""Runtime connection registry passed to side effect provider plugins."""

from collections.abc import Iterable

from app.infra.exceptions import ConnectionNotFoundError
from app.infra.side_effects.connection_config import ConnectionConfig


class ConnectionRegistry:
    """Stores side effect provider connection configs by name."""

    def __init__(self, connections: Iterable[ConnectionConfig] | None = None) -> None:
        self._connections: dict[str, ConnectionConfig] = {}
        for connection in connections or ():
            self.register(connection)

    def register(self, connection: ConnectionConfig) -> None:
        """Registers a connection config by name."""
        self._connections[connection.name] = connection

    def get(self, name: str) -> ConnectionConfig:
        """Returns a registered connection config by name."""
        try:
            return self._connections[name]
        except KeyError as exc:
            raise ConnectionNotFoundError(name=name) from exc

    def list_by_provider(self, provider: str) -> list[ConnectionConfig]:
        """Returns connection configs for a provider type."""
        return [
            connection
            for connection in self._connections.values()
            if connection.provider == provider
        ]
