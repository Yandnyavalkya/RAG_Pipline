from typing import Optional

from backend.app.core.database import get_database
from backend.app.repositories.base import (
    owned_filter,
    serialize_document,
    utc_now,
)


class ConversationRepository:
    def collection(self):
        return get_database().conversations

    async def create(
        self,
        user_id: str,
        document_id: str,
        title: str,
    ) -> dict:
        now = utc_now()
        document = {
            "user_id": user_id,
            "document_id": document_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_document(document)

    async def find_owned(
        self,
        conversation_id: str,
        user_id: str,
    ) -> Optional[dict]:
        query = owned_filter(user_id, conversation_id)
        if query is None:
            return None
        return serialize_document(await self.collection().find_one(query))

    async def list_by_document(
        self,
        user_id: str,
        document_id: str,
    ) -> list[dict]:
        cursor = self.collection().find(
            {"user_id": user_id, "document_id": document_id}
        ).sort("updated_at", -1)
        return [serialize_document(item) async for item in cursor]

    async def touch(self, conversation_id: str, user_id: str) -> None:
        query = owned_filter(user_id, conversation_id)
        if query is None:
            return
        await self.collection().update_one(
            query,
            {"$set": {"updated_at": utc_now()}},
        )

    async def delete_by_document(self, user_id: str, document_id: str) -> int:
        result = await self.collection().delete_many(
            {"user_id": user_id, "document_id": document_id}
        )
        return result.deleted_count
