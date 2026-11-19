import asyncio

from backend.app.core.exceptions import bad_request, not_found
from backend.app.rag.rag_adapter import answer_question
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.message_repository import MessageRepository
from backend.app.services.document_service import DocumentService


class ChatService:
    def __init__(self):
        self.documents = DocumentRepository()
        self.conversations = ConversationRepository()
        self.messages = MessageRepository()

    async def create_conversation(self, user_id: str, document_id: str, title: str | None = None) -> dict:
        doc = await DocumentService().get(document_id, user_id)
        if doc["status"] != "ready":
            raise bad_request("Wait for document processing to finish before starting a chat")
        return await self.conversations.create(user_id, document_id, (title or doc["original_filename"])[:200])

    async def ask(self, user_id: str, payload: dict) -> dict:
        doc = await DocumentService().get(payload["document_id"], user_id)
        if doc["status"] != "ready":
            raise bad_request("This document is not ready for questions yet")
        conversation = await self.conversations.find_owned(payload["conversation_id"], user_id)
        if conversation is None or conversation["document_id"] != payload["document_id"]:
            raise not_found("Conversation not found for this document")
        previous = await self.messages.list_by_conversation(conversation["id"], user_id)
        history = []
        for index in range(0, len(previous) - 1, 2):
            if previous[index].get("role") == "user" and previous[index + 1].get("role") == "assistant":
                history.append({"question": previous[index]["content"], "answer": previous[index + 1]["content"]})
        question = payload["question"].strip()
        result = await asyncio.to_thread(answer_question, question, history[-5:], payload["document_id"], user_id)
        sources = [{
            "document_id": source.get("document_id"),
            "filename": source.get("document") or doc["original_filename"],
            "page": source.get("page"), "chunk_id": source.get("chunk_id"),
            "excerpt": source.get("excerpt", ""),
        } for source in result.get("sources", [])]
        await self.messages.create(conversation["id"], user_id, "user", question)
        assistant_message = await self.messages.create(
            conversation["id"], user_id, "assistant", result["answer"],
            confidence=result.get("confidence"), sources=sources,
        )
        await self.conversations.touch(conversation["id"], user_id)
        related = result.get("related_questions") or []
        if not related:
            related = (await DocumentService().suggestions(payload["document_id"], user_id))["suggestions"]
        return {
            "status": result.get("status", "success"), "conversation_id": conversation["id"],
            "message_id": assistant_message["id"], "question": question,
            "answer": result["answer"], "question_type": result.get("question_type"),
            "confidence": result.get("confidence") or {"level": "none", "score": 0, "signals": {}},
            "sources": sources, "related_questions": related,
        }

    async def history(self, conversation_id: str, user_id: str) -> dict:
        conversation = await self.conversations.find_owned(conversation_id, user_id)
        if conversation is None:
            raise not_found("Conversation not found")
        return {"conversation_id": conversation_id, "document_id": conversation["document_id"],
                "messages": await self.messages.list_by_conversation(conversation_id, user_id)}
