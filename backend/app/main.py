from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import api_router
from backend.app.core.config import (
    API_V1_PREFIX,
    APP_NAME,
    FRONTEND_ORIGINS,
)
from backend.app.core.database import (
    close_mongo,
    connect_to_mongo,
    is_testing,
    mongodb_status,
)
from backend.app.middleware.error_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not is_testing():
        await connect_to_mongo()
    try:
        yield
    finally:
        if not is_testing():
            await close_mongo()


app = FastAPI(
    title=APP_NAME,
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health():
    """Liveness probe. Does not return secrets or credentials."""

    mongo_state = mongodb_status()
    status_value = "ok" if mongo_state == "connected" or is_testing() else "degraded"

    return {
        "status": status_value,
        "service": APP_NAME,
        "api_version": "v1",
        "mongodb": mongo_state,
    }
