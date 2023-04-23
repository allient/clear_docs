from fastapi import APIRouter
from app.api.v1.endpoints import (
    openai,
    qdrant,
    user,
    auth,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(openai.router, prefix="/openai", tags=["openai"])
api_router.include_router(qdrant.router, prefix="/qdrant", tags=["qdrant"])
