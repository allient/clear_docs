from collections.abc import AsyncGenerator
from uuid import UUID
from fastapi import Depends

import requests
from app.utils.neural_searcher import NeuralSearcher
from fastapi.security import OAuth2PasswordBearer
from app.models.user_model import User
from app import crud
from app.core.config import settings
from app.db.session import SessionLocal
from qdrant_client import QdrantClient
from sqlmodel.ext.asyncio.session import AsyncSession
import redis.asyncio as aioredis
from redis.asyncio import Redis
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI


reusable_oauth2 = OAuth2PasswordBearer(
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
    client: QdrantClient = QdrantClient(
        url=settings.QDRANT_CLOUD_URL, api_key=settings.QDRANT_CLOUD_API_KEY
    )
    return client


def get_langchain_embeddings() -> OpenAIEmbeddings:
    embeddings: OpenAIEmbeddings = OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY
    )
    return embeddings


def get_chat_openai() -> ChatOpenAI:
    chat = ChatOpenAI(
        temperature=0,
        openai_api_key=settings.OPENAI_API_KEY,
        model_name="gpt-3.5-turbo",
    )
    return chat



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
    _request=Depends(reusable_oauth2),
):
    pass