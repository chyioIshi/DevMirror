from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import AppSettings
from app.infra.db.mongo.documents import MockDocument, RequestLogDocument


async def init_mongo(settings: AppSettings) -> AsyncMongoClient:
    client = AsyncMongoClient(settings.mongo_dsn)
    await init_beanie(
        database=client[settings.mongo_database],
        document_models=[MockDocument, RequestLogDocument],
    )
    return client
