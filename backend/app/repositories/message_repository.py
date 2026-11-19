from typing import Optional

from backend.app.core.database import get_database
from backend.app.repositories.base import (
    owned_filter,
    serialize_document,
    utc_now,
)


class MessageRepository:
    def collection(self):
        return get_database().messages

    async def create(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        confidence: Optional[dict] = None,
        sources: Optional[list] = None,
    ) -> dict:
        document = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "confidence": confidence,
            "sources": sources or [],
            "created_at": utc_now(),
        }
        result = await self.collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_document(document)

    async def list_by_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> list[dict]:
        cursor = self.collection().find(
            {"conversation_id": conversation_id, "user_id": user_id}
        ).sort("created_at", 1)
        return [serialize_document(item) async for item in cursor]

    async def find_owned(self, message_id: str, user_id: str) -> Optional[dict]:
        query = owned_filter(user_id, message_id)
        if query is None:
            return None
        return serialize_document(await self.collection().find_one(query))

    async def delete_by_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> int:
        result = await self.collection().delete_many(
            {"user_id": user_id, "conversation_id": conversation_id}
        )
        return result.deleted_count
