from pathlib import Path

from config import BASE_DIR, get_env


APP_NAME = "RAG Document Intelligence API"
API_V1_PREFIX = "/api/v1"

UPLOAD_DIR = Path(
    get_env("UPLOAD_DIR", str(BASE_DIR / "backend" / "uploads"))
)
MAX_UPLOAD_SIZE_MB = int(get_env("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf"}

MONGODB_URI = get_env("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = get_env("MONGODB_DATABASE", "rag_platform")

JWT_SECRET = get_env("JWT_SECRET")
JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in get_env(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
ADMIN_EMAILS = {
    email.strip().lower()
    for email in get_env("ADMIN_EMAILS", "").split(",")
    if email.strip()
}


def mongodb_is_configured() -> bool:
    return bool(MONGODB_URI)


def jwt_is_configured() -> bool:
    return bool(JWT_SECRET)
