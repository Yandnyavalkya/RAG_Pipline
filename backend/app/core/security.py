from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
)


def _require_jwt_secret() -> str:
    if not JWT_SECRET:
        raise ValueError(
            "JWT_SECRET is missing. Set it in the environment or .env file."
        )
    return JWT_SECRET


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def create_access_token(user_id: str, email: str) -> tuple[str, datetime]:
    secret = _require_jwt_secret()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expires_at,
    }
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> dict:
    secret = _require_jwt_secret()
    return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
