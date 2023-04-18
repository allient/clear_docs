from collections.abc import AsyncGenerator
from uuid import UUID
from app.utils.neural_searcher import NeuralSearcher
from fastapi import Depends, HTTPException, status
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


async def get_general_meta() -> IMetaGeneral:
    current_roles = await crud.role.get_multi(skip=0, limit=100)
    return IMetaGeneral(roles=current_roles)


def get_current_user(required_roles: list[str] = None) -> User:
    async def current_user(
        token: str = Depends(reusable_oauth2),
        redis_client: Redis = Depends(get_redis_client),
    ) -> User:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
            )
        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        user_id = payload["sub"]
        valid_access_tokens = await get_valid_tokens(
            redis_client, user_id, TokenType.ACCESS
        )
        if valid_access_tokens and token not in valid_access_tokens:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        user: User = await crud.user.get(id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        if required_roles:
            is_valid_role = False
            for role in required_roles:
                if role == user.role.name:
                    is_valid_role = True

            if not is_valid_role:
                raise HTTPException(
                    status_code=403,
                    detail=f"""Role "{required_roles}" is required for this action""",
                )

        return user

    return current_user


async def current_user1(
    request=Depends(oauth2_scheme),
    session_: SessionContainer = Depends(verify_session()),
) -> User:
    user_id: UUID = session_.get_user_id()
    user: User = await crud.user.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
