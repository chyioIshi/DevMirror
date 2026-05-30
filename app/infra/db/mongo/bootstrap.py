"""MongoDB connection initialization and Beanie document registration."""

from inspect import isawaitable
from typing import Any

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import AppSettings
from app.infra.db.mongo.documents import MockDocument, RequestLogDocument


async def init_mongo(settings: AppSettings) -> AsyncMongoClient[dict[str, Any]]:
    """Initializes MongoDB connection and registers Beanie document models.

    Args:
        settings: Application settings with MongoDB connection parameters.

    Returns:
        Initialized asynchronous MongoDB client.
    """
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(str(settings.mongo_dsn))
    await init_beanie(
        database=client[settings.mongo_database],
        document_models=[MockDocument, RequestLogDocument],
    )
    return client


async def close_mongo(client: AsyncMongoClient[dict[str, Any]]) -> None:
    """Closes a MongoDB client.

    Args:
        client: Asynchronous MongoDB client to close.
    """
    close_result = client.close()
    if isawaitable(close_result):
        await close_result
