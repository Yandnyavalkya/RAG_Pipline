from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    document_id: str
    conversation_id: str
    question: str = Field(min_length=1, max_length=4000)


class CreateConversationRequest(BaseModel):
    document_id: str
    title: Optional[str] = Field(default=None, max_length=200)


class ConversationResponse(BaseModel):
    id: str
    document_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConfidenceResponse(BaseModel):
    level: str
    score: float
    signals: Dict[str, Any] = Field(default_factory=dict)


class SourceResponse(BaseModel):
    document_id: Optional[str] = None
    filename: str
    page: Optional[object] = None
    chunk_id: Optional[str] = None
    excerpt: str = ""


class ChatAskResponse(BaseModel):
    status: str
    conversation_id: str
    message_id: Optional[str] = None
    question: str
    answer: str
    question_type: Optional[str] = None
    confidence: ConfidenceResponse
    sources: List[SourceResponse] = Field(default_factory=list)
    related_questions: List[str] = Field(default_factory=list)


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    confidence: Optional[Dict[str, Any]] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    document_id: str
    messages: List[ChatMessageResponse]
