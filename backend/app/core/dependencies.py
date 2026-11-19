"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.exceptions import forbidden, unauthorized
from backend.app.core.config import ADMIN_EMAILS
from backend.app.repositories.user_repository import UserRepository
from backend.app.core.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if credentials is None:
        raise unauthorized()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token subject is missing")
        return str(user_id)
    except Exception as exc:
        raise unauthorized() from exc


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_current_admin_id(user_id: CurrentUserId) -> str:
    user = await UserRepository().find_by_id(user_id)
    if user is None or user.get("email", "").lower() not in ADMIN_EMAILS:
        raise forbidden("Admin access is required to review feedback")
    return user_id


AdminUserId = Annotated[str, Depends(get_current_admin_id)]
