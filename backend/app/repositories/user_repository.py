from typing import Optional

from backend.app.core.database import get_database
from backend.app.repositories.base import (
    parse_object_id,
    serialize_document,
    utc_now,
)


class UserRepository:
    def collection(self):
        return get_database().users

    async def create(self, name: str, email: str, password_hash: str) -> dict:
        now = utc_now()
        document = {
            "name": name.strip(),
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_document(document)

    async def find_by_email(self, email: str) -> Optional[dict]:
        return await self.collection().find_one({"email": email.lower().strip()})

    async def find_by_id(self, user_id: str) -> Optional[dict]:
        object_id = parse_object_id(user_id)
        if object_id is None:
            return None
        return await self.collection().find_one({"_id": object_id})
