"""
Async MongoDB connection factory using Motor.

Provides a singleton database instance with connection pooling.
"""

import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import MONGODB_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    """Return the shared database handle, creating the client on first call."""
    global _client, _db

    if _db is None:
        _client = AsyncIOMotorClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=30_000,
            connectTimeoutMS=30_000,
            maxPoolSize=50,
            minPoolSize=3,
        )
        _db = _client[MONGO_DB_NAME]
        logger.info(f"MongoDB connection pool created (db: {_db.name})")

    return _db


async def init_db() -> AsyncIOMotorDatabase:
    """Initialize database and create indexes."""
    db = get_db()

    from app.database.models import init_db_indexes
    await init_db_indexes()

    return db


async def close_db():
    """Close the MongoDB connection pool."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
