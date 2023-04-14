from fastapi import APIRouter
from app.api.v1.endpoints import (
    openai,
    user,
    login,
    role,
)

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(role.router, prefix="/role", tags=["role"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(
    openai.router, prefix="/openai", tags=["openai"]
)
