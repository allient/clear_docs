import time
from app.models.user_model import User
from app.schemas.common_schema import IChatCompletionResponse
from app.schemas.response_schema import IPostResponseBase, create_response
from app.utils.chatgpt import get_embedding, num_tokens_from_messages
from asyncer import asyncify
from fastapi import APIRouter, Body, Depends
from langchain import LLMChain
from langchain.embeddings import OpenAIEmbeddings
import openai
from pydantic import BaseModel
from fastapi_limiter.depends import RateLimiter
from app.api.deps import get_current_user, get_langchain_embeddings, get_chat_openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

router = APIRouter()


class Input(BaseModel):
    prompt: str


class Inputs(BaseModel):
    prompts: list[str]


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
    "/embeddings",
    dependencies=[
        Depends(RateLimiter(times=200, hours=24)),
    ],
)
async def generate_embeddings(
    body: Inputs,
    current_user: User = Depends(get_current_user),
    embeddings: OpenAIEmbeddings = Depends(get_langchain_embeddings),
) -> IPostResponseBase[list[list[float]]]:
    doc_result = await asyncify(embeddings.embed_documents)(texts=body.prompts)
    return create_response(data=doc_result, message="Embedding got succesfully")


@router.post(
    "/text_generation",
    dependencies=[
        Depends(RateLimiter(times=200, hours=24)),
    ],
)
async def text_generation_prediction(
    body: Input,
    chat: ChatOpenAI = Depends(get_chat_openai),
    current_user: User = Depends(get_current_user),
) -> IPostResponseBase[dict]:
    """
    Async text generation using a NLP model from transformers libray (Not reommended for long time inferences)
    """
    messages = [
        SystemMessage(content="You are a helpful help desk assistant."),
        HumanMessage(content="Which is the capital of Ecuador?"),
        AIMessage(content="The capital of Ecuador is Quito."),
        HumanMessage(content=body.prompt),
    ]

    response = await asyncify(chat)(messages=messages)
    return create_response(message="Prediction got succesfully", data=response.dict())


@router.post(
    "/chain",
    dependencies=[
        Depends(RateLimiter(times=200, hours=24)),
    ],
)
async def generate_template_chain(
    body: Input,
    chat: ChatOpenAI = Depends(get_chat_openai),
    current_user: User = Depends(get_current_user),
) -> IPostResponseBase[str]:
    template = "Tu eres un asistente legal capaz de explicar conceptos de manera simple y amigable."
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    example_human = HumanMessagePromptTemplate.from_template("Hola")
    example_ai = AIMessagePromptTemplate.from_template("Hola que tal?")
    human_template = "{text}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    response = await asyncify(chain.run)(text=body.prompt)    

    
    return create_response(message="Prediction got succesfully", data=response)
