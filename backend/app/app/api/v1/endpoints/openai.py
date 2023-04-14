from app.schemas.common_schema import IChatCompletionResponse
from app.schemas.response_schema import IPostResponseBase, create_response
from app.utils.chatgpt import num_tokens_from_messages
from asyncer import asyncify
from fastapi import APIRouter
from app.utils.fastapi_globals import g
import openai
from pydantic import BaseModel

router = APIRouter()


@router.post("/sentiment_analysis")
async def sentiment_analysis_prediction(
    prompt: str = "Fastapi is awesome",
) -> IPostResponseBase:
    """
    Gets a sentimental analysis predition using a NLP model from transformers libray
    """
    sentiment_model = g.sentiment_model
    prediction = sentiment_model(prompt)
    return create_response(message="Prediction got succesfully", data=prediction)


@router.post("/text_generation")
async def text_generation_prediction(
    prompt: str = "Superman is awesome because",
) -> IPostResponseBase:
    """
    Sync text generation using a NLP model from transformers libray (Not reommended for long time inferences)
    """
    text_generator_model = g.text_generator_model
    prediction = text_generator_model(prompt)
    return create_response(message="Prediction got succesfully", data=prediction)


class Input(BaseModel):
    prompt: str


@router.post("/num_tokens_from_messages")
async def get_num_tokens_from_messages(
    body: Input,
) -> IPostResponseBase[str]:
    data = num_tokens_from_messages(
        messages=[
            {"role": "system", "content": "You are a helpful help desk assistant."},
            {"role": "user", "content": "Which is the capital of Ecuador?"},
            {
                "role": "assistant",
                "content": "The capital of Ecuador is Quito.",
            },
            {"role": "user", "content": "Responde lo mismo pero en español"},
        ]
    )
    print("data", data)
    return create_response(data="hi")


@router.post("/")
async def create_completition(
    body: Input,
) -> IPostResponseBase[IChatCompletionResponse]:
    """
    An example "Hello world" FastAPI route.
    """
    response: IChatCompletionResponse = await asyncify(openai.ChatCompletion.create)(
        model="gpt-3.5-turbo",
        temperature=0.1,
        user="001",
        messages=[
            {"role": "system", "content": "You are a helpful help desk assistant."},
            {"role": "user", "content": "Which is the capital of Ecuador?"},
            {
                "role": "assistant",
                "content": "The capital of Ecuador is Quito.",
            },
            {"role": "user", "content": "Responde lo mismo pero en español"},
        ],
    )

    return create_response(data=response)
