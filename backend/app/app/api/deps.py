import base64
from collections.abc import AsyncGenerator
import json
from urllib.request import urlopen
from uuid import UUID
from app.auth.decode_verify_jwt import verify_cognito_token
from fastapi import Depends, HTTPException
import jwt
import rsa
from app.core import security
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
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/access-token"
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



def get_user_id(token: str = Depends(reusable_oauth2)) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail='You missed the bearer token')
    try:
        # Decode and verify the token using decode-verify-jwt
        decoded_token = verify_cognito_token(token)
        
        # Get the user attributes from the decoded token            
        user_id = decoded_token["sub"]
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail=f"{e}")
    
    return user_id

async def get_current_user(token: str = Depends(reusable_oauth2)) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail='You missed the bearer token')
    try:
        # Decode and verify the token using decode-verify-jwt
        decoded_token = verify_cognito_token(token)
        
        # Get the user attributes from the decoded token            
        user_id = decoded_token["sub"]
        user: User = await crud.user.get(id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")        
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail=f"{e}")
    
    return user