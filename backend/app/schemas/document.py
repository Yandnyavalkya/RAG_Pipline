from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_size: int
    file_type: str
    status: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    processing_error: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


class SuggestionResponse(BaseModel):
    document_id: str
    status: str
    suggestions: List[str] = Field(default_factory=list)
