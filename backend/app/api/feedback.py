from fastapi import APIRouter

from backend.app.core.dependencies import AdminUserId, CurrentUserId
from backend.app.schemas.feedback import (
    FeedbackListResponse,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackStatusUpdate,
)
from backend.app.services.feedback_service import FeedbackService

router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(payload: FeedbackRequest, user_id: CurrentUserId):
    return await FeedbackService().submit(user_id, payload.model_dump())


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(user_id: CurrentUserId):
    return {"feedback": await FeedbackService().list(user_id)}


@router.get("/review", response_model=FeedbackListResponse)
async def list_feedback_for_review(admin_id: AdminUserId):
    return {"feedback": await FeedbackService().list_all()}


@router.patch("/{feedback_id}/status", response_model=FeedbackResponse)
async def update_feedback_status(feedback_id: str, payload: FeedbackStatusUpdate, admin_id: AdminUserId):
    return await FeedbackService().review(feedback_id, payload.status)
