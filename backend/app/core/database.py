import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient

from backend.app.core.config import MONGODB_DATABASE, MONGODB_URI

logger = logging.getLogger("backend.mongo")

mongo_client = None
database = None


def is_testing() -> bool:
    return os.getenv("TESTING", "").strip() in {"1", "true", "True"}


async def connect_to_mongo() -> None:
    global mongo_client, database

    mongo_client = AsyncIOMotorClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=8000,
    )
    database = mongo_client[MONGODB_DATABASE]
    await database.command("ping")
    await ensure_indexes()
    logger.info("MongoDB connected to database %s", MONGODB_DATABASE)


async def ensure_indexes() -> None:
    db = get_database()

    await db.users.create_index("email", unique=True)
    await db.documents.create_index("user_id")
    await db.documents.create_index([("user_id", 1), ("created_at", -1)])
    await db.conversations.create_index([("user_id", 1), ("document_id", 1)])
    await db.conversations.create_index([("user_id", 1), ("updated_at", -1)])
    await db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
    await db.messages.create_index([("user_id", 1), ("conversation_id", 1)])
    await db.feedback.create_index([("user_id", 1), ("created_at", -1)])
    await db.feedback.create_index("message_id")


async def close_mongo() -> None:
    global mongo_client, database

    if mongo_client is not None:
        mongo_client.close()

    mongo_client = None
    database = None


def get_database():
    if database is None:
        raise RuntimeError("MongoDB is not connected.")
    return database


def mongodb_status() -> str:
    if database is None:
        return "disconnected"
    return "connected"
