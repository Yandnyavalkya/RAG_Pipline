from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_object_id(value: Any) -> Optional[ObjectId]:
    if isinstance(value, ObjectId):
        return value
    if value is None:
        return None
    text = str(value)
    if not ObjectId.is_valid(text):
        return None
    return ObjectId(text)


def owned_filter(user_id: str, resource_id: Any) -> Optional[dict]:
    """Always include user_id so IDs from other users cannot be selected."""

    object_id = parse_object_id(resource_id)
    if object_id is None or not user_id:
        return None
    return {"_id": object_id, "user_id": user_id}


def serialize_document(document: Optional[dict]) -> Optional[dict]:
    if document is None:
        return None

    payload = dict(document)
    payload["id"] = str(payload.pop("_id"))
    payload.pop("password_hash", None)
    return payload
