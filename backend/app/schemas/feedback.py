from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    helpful = "helpful"
    incorrect_answer = "incorrect_answer"
    missing_information = "missing_information"
    incorrect_citation = "incorrect_citation"
    other = "other"


class FeedbackRequest(BaseModel):
    document_id: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    question: str = Field(min_length=1)
    original_answer: str = Field(min_length=1)
    feedback_type: FeedbackType
    correction: Optional[str] = None
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    document_id: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    question: str
    original_answer: str
    feedback_type: FeedbackType
    correction: Optional[str] = None
    comment: Optional[str] = None
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    submitted_by: Optional[str] = None


class FeedbackListResponse(BaseModel):
    feedback: List[FeedbackResponse]


class FeedbackStatusUpdate(BaseModel):
    status: str = Field(pattern="^(submitted|reviewed|resolved)$")
