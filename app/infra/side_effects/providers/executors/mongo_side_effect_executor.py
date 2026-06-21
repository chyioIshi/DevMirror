"""pymongo-backed MongoDB side effect executor."""

import asyncio
from dataclasses import dataclass
from inspect import isawaitable
from typing import Any

from pymongo import AsyncMongoClient as PymongoAsyncMongoClient

from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError, MongoSideEffectError
from app.infra.side_effects.connection_config import ConnectionConfig


@dataclass(slots=True, frozen=True)
class MongoSideEffectExecutorConfig:
    """Validated MongoDB executor configuration."""

    connection_name: str
    uri: str
    database: str
    server_selection_timeout_ms: int | None
    max_pool_size: int | None
    min_pool_size: int | None

    def key(self) -> tuple[str, str, str, int | None, int | None, int | None]:
        """Returns the cache key for a MongoDB client created from this config."""
        return (
            self.connection_name,
            self.uri,
            self.database,
            self.server_selection_timeout_ms,
            self.max_pool_size,
            self.min_pool_size,
        )

    def create_client_map(self) -> dict[str, Any]:
        """Returns pymongo.AsyncMongoClient params in dict."""
        params: dict[str, Any] = {"host": self.uri}
        if self.server_selection_timeout_ms is not None:
            params["serverSelectionTimeoutMS"] = self.server_selection_timeout_ms
        if self.max_pool_size is not None:
            params["maxPoolSize"] = self.max_pool_size
        if self.min_pool_size is not None:
            params["minPoolSize"] = self.min_pool_size
        return params


class AsyncMongoSideEffectExecutor:
    """Executes MongoDB side effect commands using reusable async clients."""

    def __init__(self) -> None:
        """Initializes an empty MongoDB executor cache."""
        self._clients: dict[
            tuple[str, str, str, int | None, int | None, int | None],
            PymongoAsyncMongoClient[dict[str, Any]],
        ] = {}
        self._client_lock = asyncio.Lock()

    async def insert_one(
        self,
        *,
        connection: ConnectionConfig,
        collection: str,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """Inserts one document into a MongoDB collection."""
        database = await self._database(connection)
        try:
            result = await database[collection].insert_one(document)
        except Exception as exc:
            raise MongoSideEffectError(
                "Mongo insert_one command failed",
                details={
                    "stage": "execute",
                    "operation": "db_insert",
                    "connection": connection.name,
                    "collection": collection,
                },
            ) from exc
        return {"inserted_id": str(result.inserted_id)}

    async def update_one(
        self,
        *,
        connection: ConnectionConfig,
        collection: str,
        filter_: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> dict[str, Any]:
        """Updates one document in a MongoDB collection."""
        database = await self._database(connection)
        try:
            result = await database[collection].update_one(
                filter_,
                update,
                upsert=upsert,
            )
        except Exception as exc:
            raise MongoSideEffectError(
                "Mongo update_one command failed",
                details={
                    "stage": "execute",
                    "operation": "db_update",
                    "connection": connection.name,
                    "collection": collection,
                },
            ) from exc
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": None if result.upserted_id is None else str(result.upserted_id),
        }

    async def aclose(self) -> None:
        """Closes cached MongoDB clients."""
        async with self._client_lock:
            try:
                results: list[object] = await asyncio.gather(
                    *(self._close_client(client) for client in self._clients.values()),
                    return_exceptions=True,
                )
            finally:
                self._clients.clear()

        errors = [str(result) for result in results if isinstance(result, Exception)]
        if errors:
            raise MongoSideEffectError(
                "Mongo client close failed",
                details={"stage": "close", "errors": errors},
            )

    async def _database(self, connection: ConnectionConfig) -> Any:
        config = self._client_config(connection)
        client = await self._client(config)
        return client[config.database]

    async def _client(
        self, config: MongoSideEffectExecutorConfig
    ) -> PymongoAsyncMongoClient[dict[str, Any]]:
        key = config.key()
        client = self._clients.get(key)
        if client is not None:
            return client

        async with self._client_lock:
            client = self._clients.get(key)
            if client is not None:
                return client

            try:
                client = PymongoAsyncMongoClient(**config.create_client_map())
            except Exception as exc:
                raise MongoSideEffectError(
                    "Mongo client creation failed",
                    details={"stage": "connect", "connection": config.connection_name},
                ) from exc

            self._clients[key] = client
            return client

    def _client_config(self, connection: ConnectionConfig) -> MongoSideEffectExecutorConfig:
        min_pool_size = SideEffectProviderValidation.optional_non_negative_int(
            connection.settings,
            "min_pool_size",
            "connection.settings.min_pool_size",
            subject="Mongo",
        )
        max_pool_size = SideEffectProviderValidation.optional_positive_int(
            connection.settings,
            "max_pool_size",
            "connection.settings.max_pool_size",
            subject="Mongo",
        )
        if (
            min_pool_size is not None
            and max_pool_size is not None
            and max_pool_size < min_pool_size
        ):
            raise InvalidSideEffectProviderConfigError(
                "Mongo connection.settings.max_pool_size must be greater than or equal to min_pool_size",
                details={"field": "connection.settings.max_pool_size"},
            )

        return MongoSideEffectExecutorConfig(
            connection_name=connection.name,
            uri=SideEffectProviderValidation.required_string(
                connection.settings,
                "uri",
                "connection.settings.uri",
                subject="Mongo",
            ),
            database=SideEffectProviderValidation.required_string(
                connection.settings,
                "database",
                "connection.settings.database",
                subject="Mongo",
            ),
            server_selection_timeout_ms=SideEffectProviderValidation.optional_positive_int(
                connection.settings,
                "server_selection_timeout_ms",
                "connection.settings.server_selection_timeout_ms",
                subject="Mongo",
            ),
            max_pool_size=max_pool_size,
            min_pool_size=min_pool_size,
        )

    async def _close_client(self, client: PymongoAsyncMongoClient[dict[str, Any]]) -> None:
        close_result = client.close()
        if isawaitable(close_result):
            await close_result
