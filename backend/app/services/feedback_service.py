"""Store user corrections for review; feedback never silently changes answers."""
from __future__ import annotations

from backend.app.core.exceptions import bad_request, not_found
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.repositories.feedback_repository import FeedbackRepository
from backend.app.repositories.message_repository import MessageRepository
from backend.app.repositories.user_repository import UserRepository


class FeedbackService:
    def __init__(self):
        self.documents = DocumentRepository()
        self.feedback = FeedbackRepository()
        self.messages = MessageRepository()
        self.conversations = ConversationRepository()

    async def submit(self, user_id: str, payload: dict) -> dict:
        doc = await self.documents.find_owned(payload["document_id"], user_id)
        if doc is None:
            raise not_found("Document not found")
        message_id = payload.get("message_id")
        if message_id:
            message = await self.messages.find_owned(message_id, user_id)
            if message is None or message.get("role") != "assistant":
                raise not_found("Answer not found")
            conversation = await self.conversations.find_owned(message["conversation_id"], user_id)
            if conversation is None or conversation["document_id"] != payload["document_id"]:
                raise not_found("Answer not found")
        if payload.get("conversation_id"):
            conversation = await self.conversations.find_owned(payload["conversation_id"], user_id)
            if conversation is None or conversation["document_id"] != payload["document_id"]:
                raise not_found("Conversation not found")
        if payload["feedback_type"] != "helpful" and not (payload.get("correction", "").strip() or payload.get("comment", "").strip()):
            raise bad_request("Add a correction or comment so the team can review your feedback")
        payload["feedback_type"] = payload["feedback_type"].value if hasattr(payload["feedback_type"], "value") else payload["feedback_type"]
        return await self.feedback.create(user_id, payload)

    async def list(self, user_id: str) -> list[dict]:
        return await self.feedback.list_by_user(user_id)

    async def list_all(self) -> list[dict]:
        rows = await self.feedback.list_all()
        users = UserRepository()
        for row in rows:
            owner = await users.find_by_id(row.get("user_id"))
            row["submitted_by"] = owner.get("email") if owner else "Unknown user"
        return rows

    async def review(self, feedback_id: str, status: str) -> dict:
        result = await self.feedback.update_status(feedback_id, status)
        if result is None:
            raise not_found("Feedback not found")
        return result
