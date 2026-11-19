from typing import Optional

from backend.app.core.database import get_database
from backend.app.repositories.base import (
    owned_filter,
    serialize_document,
    utc_now,
)


class FeedbackRepository:
    def collection(self):
        return get_database().feedback

    async def create(self, user_id: str, payload: dict) -> dict:
        document = {
            "user_id": user_id,
            "document_id": payload["document_id"],
            "conversation_id": payload.get("conversation_id"),
            "message_id": payload.get("message_id"),
            "question": payload["question"],
            "original_answer": payload["original_answer"],
            "feedback_type": payload["feedback_type"],
            "correction": payload.get("correction"),
            "comment": payload.get("comment"),
            "status": payload.get("status", "submitted"),
            "created_at": utc_now(),
        }
        result = await self.collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_document(document)

    async def list_by_user(self, user_id: str) -> list[dict]:
        cursor = self.collection().find({"user_id": user_id}).sort(
            "created_at", -1
        )
        return [serialize_document(item) async for item in cursor]

    async def list_all(self) -> list[dict]:
        cursor = self.collection().find({}).sort("created_at", -1)
        return [serialize_document(item) async for item in cursor]

    async def update_status(self, feedback_id: str, status: str) -> Optional[dict]:
        from bson import ObjectId
        from pymongo import ReturnDocument

        if not ObjectId.is_valid(feedback_id):
            return None
        result = await self.collection().find_one_and_update(
            {"_id": ObjectId(feedback_id)},
            {"$set": {"status": status, "reviewed_at": utc_now()}},
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(result)

    async def find_owned(
        self,
        feedback_id: str,
        user_id: str,
    ) -> Optional[dict]:
        query = owned_filter(user_id, feedback_id)
        if query is None:
            return None
        return serialize_document(await self.collection().find_one(query))
