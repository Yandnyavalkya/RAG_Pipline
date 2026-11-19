from fastapi import APIRouter

from backend.app.core.dependencies import CurrentUserId
from backend.app.schemas.chat import (
    ChatAskRequest,
    ChatAskResponse,
    ConversationHistoryResponse,
    ConversationResponse,
    CreateConversationRequest,
)
from backend.app.services.chat_service import ChatService

router = APIRouter()


@router.post("/ask", response_model=ChatAskResponse)
async def ask_question(payload: ChatAskRequest, user_id: CurrentUserId):
    return await ChatService().ask(user_id, payload.model_dump())


@router.get(
    "/history/{conversation_id}",
    response_model=ConversationHistoryResponse,
)
async def get_conversation_history(conversation_id: str, user_id: CurrentUserId):
    return await ChatService().history(conversation_id, user_id)


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(payload: CreateConversationRequest, user_id: CurrentUserId):
    return await ChatService().create_conversation(user_id, payload.document_id, payload.title)
