from fastapi import APIRouter

from backend.app.core.dependencies import CurrentUserId
from backend.app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from backend.app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterRequest):
    return await AuthService().register(payload.model_dump())


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    return await AuthService().login(payload.email, payload.password)


@router.get("/me", response_model=UserResponse)
async def read_current_user(user_id: CurrentUserId):
    return await AuthService().get_user(user_id)
