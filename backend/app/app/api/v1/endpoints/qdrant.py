from app.api.deps import get_neural_searcher
from app.schemas.response_schema import IPostResponseBase, create_response
from app.utils.neural_searcher import NeuralSearcher
from asyncer import asyncify
from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

router = APIRouter()


@router.post(
    "/search",
    dependencies=[
        Depends(RateLimiter(times=100, hours=24)),
    ],
)
async def sentiment_analysis_prediction(
    prompt: str = "Good food",
    neural_seacher: NeuralSearcher = Depends(get_neural_searcher("my_docs")),
) -> IPostResponseBase[list[dict]]:
    """
    Gets a sentimental analysis predition using a NLP model from transformers libray
    """

    hits = await asyncify(neural_seacher.search)(text=prompt)

    return create_response(data=hits)
