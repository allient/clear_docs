from fastapi import APIRouter
from app.api.v1.endpoints import (
    openai,
    qdrant,
    user,
    login,
)

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(openai.router, prefix="/openai", tags=["openai"])
api_router.include_router(qdrant.router, prefix="/qdrant", tags=["qdrant"])
