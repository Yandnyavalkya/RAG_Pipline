from pymongo.errors import DuplicateKeyError

from backend.app.core.exceptions import conflict, unauthorized
from backend.app.core.config import ADMIN_EMAILS
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self):
        self.users = UserRepository()

    @staticmethod
    def _public(user: dict) -> dict:
        email = user["email"].lower()
        return {"id": str(user.get("id") or user.get("_id")), "name": user["name"],
                "email": email, "role": "admin" if email in ADMIN_EMAILS else "user",
                "created_at": user.get("created_at")}

    def _response(self, user: dict) -> dict:
        public_user = self._public(user)
        token, _ = create_access_token(public_user["id"], public_user["email"])
        return {"access_token": token, "token_type": "bearer", "user": public_user}

    async def register(self, payload: dict) -> dict:
        try:
            user = await self.users.create(payload["name"], payload["email"], hash_password(payload["password"]))
        except DuplicateKeyError as exc:
            raise conflict("An account with this email already exists") from exc
        return self._response(user)

    async def login(self, email: str, password: str) -> dict:
        user = await self.users.find_by_email(email)
        if user is None or not verify_password(password, user.get("password_hash", "")):
            raise unauthorized("Email or password is incorrect")
        return self._response(user)

    async def get_user(self, user_id: str) -> dict:
        user = await self.users.find_by_id(user_id)
        if user is None:
            raise unauthorized()
        return self._public(user)
