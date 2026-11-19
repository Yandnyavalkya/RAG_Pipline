from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse

from backend.app.core.dependencies import CurrentUserId
from backend.app.core.exceptions import not_found
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.repositories.message_repository import MessageRepository
from backend.app.services.document_service import DocumentService
from backend.app.schemas.chat import ConversationResponse
from backend.app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    SuggestionResponse,
)

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=202)
async def upload_document(background_tasks: BackgroundTasks, user_id: CurrentUserId, file: UploadFile = File(...)):
    return await DocumentService().upload(user_id, file, background_tasks)


@router.get("", response_model=DocumentListResponse)
async def list_documents(user_id: CurrentUserId):
    return {"documents": await DocumentService().list(user_id)}


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, user_id: CurrentUserId):
    return await DocumentService().get(document_id, user_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, user_id: CurrentUserId):
    record = await DocumentService().get(document_id, user_id)
    return {key: record.get(key) for key in ("id", "status", "page_count", "chunk_count", "processing_error")}


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, user_id: CurrentUserId):
    await DocumentService().delete(document_id, user_id)
    conversations = ConversationRepository()
    for conversation in await conversations.list_by_document(user_id, document_id):
        await MessageRepository().delete_by_conversation(user_id, conversation["id"])
    await conversations.delete_by_document(user_id, document_id)


@router.get("/{document_id}/conversations", response_model=list[ConversationResponse])
async def list_document_conversations(document_id: str, user_id: CurrentUserId):
    await DocumentService().get(document_id, user_id)
    return await ConversationRepository().list_by_document(user_id, document_id)


@router.get("/{document_id}/suggestions", response_model=SuggestionResponse)
async def get_document_suggestions(document_id: str, user_id: CurrentUserId):
    return await DocumentService().suggestions(document_id, user_id)


@router.get("/{document_id}/file")
async def get_document_file(document_id: str, user_id: CurrentUserId):
    doc = await DocumentService().get(document_id, user_id)
    path = doc.get("file_path")
    if not path:
        raise not_found("Document file not found")
    return FileResponse(path, media_type="application/pdf", filename=doc["original_filename"], content_disposition_type="inline")
