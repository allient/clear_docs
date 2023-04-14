from app.api.deps import get_sync_qdrant_client
from app.schemas.common_schema import IChatCompletionResponse
from app.schemas.response_schema import IPostResponseBase, create_response
from app.utils.chatgpt import get_embedding, num_tokens_from_messages
from asyncer import asyncify
from fastapi import APIRouter, Depends
from app.utils.fastapi_globals import g
import openai
from pydantic import BaseModel
from qdrant_client import QdrantClient

router = APIRouter()


@router.post("/search")
async def sentiment_analysis_prediction(
    prompt: str = "Good food",
    qdrant_client: QdrantClient = Depends(get_sync_qdrant_client),
) -> IPostResponseBase[list[dict]]:
    """
    Gets a sentimental analysis predition using a NLP model from transformers libray
    """

    new_vector = get_embedding(text=prompt)
    hits = await asyncify(qdrant_client.search)(
        collection_name="my_docs", query_vector=new_vector, limit=3
    )

    return create_response(data=hits)
