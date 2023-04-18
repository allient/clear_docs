from app.models.user_model import User
from app.schemas.common_schema import IChatCompletionResponse
from app.schemas.response_schema import IPostResponseBase, create_response
from app.utils.chatgpt import get_embedding, num_tokens_from_messages
from asyncer import asyncify
from fastapi import APIRouter, Depends
import openai
from pydantic import BaseModel
from fastapi_limiter.depends import RateLimiter
from app.api.deps import get_current_user

router = APIRouter()


class Input(BaseModel):
    prompt: str


@router.post(
    "/num_tokens_from_messages",
    dependencies=[
        Depends(RateLimiter(times=200, hours=24)),
    ],
)
async def get_num_tokens_from_messages(
    messages: list[dict[str, str]] = [
        {"role": "system", "content": "You are a helpful help desk assistant."},
        {"role": "user", "content": "Which is the capital of Ecuador?"},
    ],
    current_user: User = Depends(get_current_user),
) -> IPostResponseBase[str]:
    data = num_tokens_from_messages(messages=messages)
    # embedding = await asyncify(get_embedding)(
    #     text="I have bought several of the Vitality canned", user_id=current_user.id
    # )
    # print("embedding", len(embedding))

    return create_response(data=data)


@router.post(
    "/text_generation",
    dependencies=[
        Depends(RateLimiter(times=200, hours=24)),
    ],
)
async def text_generation_prediction(
    body: Input,
    current_user: User = Depends(get_current_user),
) -> IPostResponseBase[IChatCompletionResponse]:
    """
    Async text generation using a NLP model from transformers libray (Not reommended for long time inferences)
    """
    response: IChatCompletionResponse = await asyncify(openai.ChatCompletion.create)(
        model="gpt-3.5-turbo",
        temperature=0.1,
        user=str(current_user.id),
        messages=[
            {"role": "system", "content": "You are a helpful help desk assistant."},
            {"role": "user", "content": "Which is the capital of Ecuador?"},
            {"role": "assistant", "content": "The capital of Ecuador is Quito."},
            {"role": "user", "content": f"{body.prompt}"},
        ],
    )

    return create_response(message="Prediction got succesfully", data=response)
