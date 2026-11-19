from typing import Optional

from backend.app.core.database import get_database
from backend.app.repositories.base import (
    owned_filter,
    serialize_document,
    utc_now,
)


class DocumentRepository:
    def collection(self):
        return get_database().documents

    async def create(self, user_id: str, payload: dict) -> dict:
        now = utc_now()
        document = {
            "user_id": user_id,
            "original_filename": payload["original_filename"],
            "stored_filename": payload["stored_filename"],
            "file_path": payload["file_path"],
            "file_size": payload["file_size"],
            "file_type": payload.get("file_type", "application/pdf"),
            "status": payload.get("status", "uploaded"),
            "page_count": payload.get("page_count"),
            "chunk_count": payload.get("chunk_count"),
            "processing_error": payload.get("processing_error"),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_document(document)

    async def list_by_user(self, user_id: str) -> list[dict]:
        cursor = self.collection().find({"user_id": user_id}).sort(
            "created_at", -1
        )
        return [serialize_document(item) async for item in cursor]

    async def find_owned(self, document_id: str, user_id: str) -> Optional[dict]:
        query = owned_filter(user_id, document_id)
        if query is None:
            return None
        return serialize_document(await self.collection().find_one(query))

    async def update_owned(
        self,
        document_id: str,
        user_id: str,
        updates: dict,
    ) -> Optional[dict]:
        query = owned_filter(user_id, document_id)
        if query is None:
            return None

        payload = {**updates, "updated_at": utc_now()}
        result = await self.collection().find_one_and_update(
            query,
            {"$set": payload},
            return_document=True,
        )
        return serialize_document(result)

    async def delete_owned(self, document_id: str, user_id: str) -> bool:
        query = owned_filter(user_id, document_id)
        if query is None:
            return False
        result = await self.collection().delete_one(query)
        return result.deleted_count == 1
