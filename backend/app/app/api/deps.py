from collections.abc import AsyncGenerator
from uuid import UUID
from app.utils.neural_searcher import NeuralSearcher
from fastapi import Depends, HTTPException, Request, status
from app.utils.token import get_valid_tokens
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from app.models.user_model import User
from pydantic import ValidationError
from app import crud
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal
from qdrant_client import QdrantClient
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.common_schema import IMetaGeneral, TokenType
import redis.asyncio as aioredis
from redis.asyncio import Redis
from app.utils.auth_cookies import OAuth2PasswordBearerWithCookie
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


async def get_redis_client() -> Redis:
    redis = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        max_connections=10,
        encoding="utf8",
        decode_responses=True,
    )
    return redis


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def get_sync_qdrant_client() -> QdrantClient:
    client: QdrantClient = QdrantClient(host=settings.QDRANT_HOST, port=6333)
    return client


def get_neural_searcher(collection_name: str) -> NeuralSearcher:
    def get_searcher() -> NeuralSearcher:
        searcher: NeuralSearcher = NeuralSearcher(
            collection_name,
            openai_api_key=settings.OPENAI_API_KEY,
            url=settings.QDRANT_CLOUD_URL,
            api_key=settings.QDRANT_CLOUD_API_KEY,
            host=settings.QDRANT_HOST,
            is_cloud_qdrant=True,
        )
        return searcher

    return get_searcher


async def get_current_user(
    _request = Depends(oauth2_scheme),
    session_: SessionContainer = Depends(verify_session()),
) -> User:
    user_id: UUID = session_.get_user_id()
    user: User = await crud.user.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
