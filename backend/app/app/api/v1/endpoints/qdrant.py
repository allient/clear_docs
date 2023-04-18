from app.api.deps import get_current_user, get_neural_searcher
from app.models.user_model import User
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
async def search_on_vector_db(
    prompt: str = "Good food",
    neural_seacher: NeuralSearcher = Depends(get_neural_searcher("my_docs")),
    current_user: User = Depends(get_current_user),
) -> IPostResponseBase[list[dict]]:
    """
    Gets the nearest objects based on the prompt
    """

    hits = await asyncify(neural_seacher.search)(text=prompt, user_id=current_user.id)

    return create_response(data=hits)
