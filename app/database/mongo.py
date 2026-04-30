"""
Async MongoDB connection factory using Motor.

Provides a singleton database instance with connection pooling.
"""

import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import MONGO_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    """Return the shared database handle, creating the client on first call."""
    global _client, _db

    if _db is None:
        _client = AsyncIOMotorClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=30_000,
            connectTimeoutMS=30_000,
            maxPoolSize=50,
            minPoolSize=3,
        )
        _db = _client[MONGO_DB_NAME]
        logger.info("MongoDB connection pool created")

    return _db


async def init_db() -> AsyncIOMotorDatabase:
    """Initialize database and create indexes."""
    db = get_db()

    # Users collection indexes
    await db.users.create_index("telegram_user_id", unique=True)

    # Accounts collection indexes
    await db.accounts.create_index(
        [("user_id", 1), ("phone_masked", 1)], unique=True
    )
    await db.accounts.create_index("user_id")

    # Analytics collection indexes
    await db.analytics.create_index("user_id", unique=True)

    # Groups collection indexes
    await db.groups.create_index(
        [("user_id", 1), ("identifier", 1)], unique=True
    )
    await db.groups.create_index("user_id")

    logger.info("Database indexes ensured")
    return db


async def close_db():
    """Close the MongoDB connection pool."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
