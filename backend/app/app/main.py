import logging
from uuid import UUID, uuid4
from app.api.deps import get_redis_client, get_sync_qdrant_client
from app.schemas.common_schema import IChatResponse, IUserMessage
from app import crud
from app.utils.callback import QuestionGenCallbackHandler, StreamingLLMCallbackHandler
from app.utils.query_data import get_chain, get_chat_chain
from app.auth.decode_verify_jwt import verify_cognito_token
from app.utils.uuid6 import uuid7
from fastapi import (
    Depends,
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router as api_router_v1
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware, db
from contextlib import asynccontextmanager
from app.utils.fastapi_globals import GlobalsMiddleware
from app.core.config import settings
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from langchain.vectorstores import Qdrant
from langchain.embeddings.openai import OpenAIEmbeddings
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter
from app.models.user_model import User
from app.utils.exceptions.common_exception import IdNotFoundException


async def user_id_identifier(request: Request):
    if request.scope["type"] == "http":
        # Retrieve the Authorization header from the request
        auth_header = request.headers.get("Authorization")

        if auth_header != None:
            # Check that the header is in the correct format
            header_parts = auth_header.split()
            if len(header_parts) == 2 and header_parts[0].lower() == "bearer":
                token = header_parts[1]
                decoded_token = verify_cognito_token(token)        
                # Get the user attributes from the decoded token            
                user_id = decoded_token["sub"]
                return user_id

    if request.scope["type"] == "websocket":
        return request.scope["path"]

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]

    ip = request.client.host
    return ip + ":" + request.scope["path"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Load your API key from an environment variable or secret management service
    redis_client = await get_redis_client()
    await FastAPILimiter.init(redis_client, identifier=user_id_identifier)
    print("startup fastapi")
    yield
    await FastAPILimiter.close()
    # shutdown


# Core Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=settings.ASYNC_DATABASE_URI,
    engine_args={
        "echo": False,
        "pool_pre_ping": True,
        "pool_size": settings.POOL_SIZE,
        "max_overflow": 64,
    },
)
app.add_middleware(GlobalsMiddleware)

# Set all CORS origins enabled
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def root():
    """
    An example "Hello world" FastAPI route.
    """
    return {"message": "Hello World"}


@app.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):    
    session_id = str(uuid4())
    key: str = f'user_id:{user_id}:session:{session_id}'    
    await websocket.accept()
    redis_client = await get_redis_client()
    ws_ratelimit = WebSocketRateLimiter(times=200, hours=24)
    vector_client = get_sync_qdrant_client()
    embeddings = OpenAIEmbeddings()
    vectorstore = Qdrant(
        client=vector_client,
        collection_name="my_docs",
        embedding_function=embeddings.embed_query,
    )

    question_handler = QuestionGenCallbackHandler(websocket)
    stream_handler = StreamingLLMCallbackHandler(websocket)
    chat_history = []
    # qa_chain = get_chain(vectorstore, question_handler, stream_handler)
    qa_chain = get_chain(vectorstore, question_handler, stream_handler)
    
    # Use the below line instead of the above line to enable tracing
    # Ensure `langchain-server` is running
    # qa_chain = get_chain(vectorstore, question_handler, stream_handler, tracing=True)

    async with db():
        user = await crud.user.get_by_id_active(id=user_id)
        if user != None:            
            await redis_client.set(key, str(websocket))
    
    
    active_connection = await redis_client.get(key)
    if active_connection is None:
        await websocket.send_text(f"Error: User ID '{user_id}' not found or inactive.")
        await websocket.close()
    else:
        while True:
            try:
                # Receive and send back the client message
                data = await websocket.receive_json()
                await ws_ratelimit(websocket)
                user_message = IUserMessage.parse_obj(data)
                user_message.user_id = user_id

                resp = IChatResponse(
                    sender="you",
                    message=user_message.message,
                    type="stream",
                    message_id=str(uuid7()),
                    id=str(uuid7()),
                )
                await websocket.send_json(resp.dict())

                # # Construct a response
                start_resp = IChatResponse(
                    sender="bot", message="", type="start", message_id="", id=""
                )
                await websocket.send_json(start_resp.dict())

                result = await qa_chain.acall(
                    {"question": user_message.message, "chat_history": chat_history}
                )
                chat_history.append((user_message.message, result["answer"]))
                question_handler.update_message_id()
                stream_handler.update_message_id()
                end_resp = IChatResponse(
                    sender="bot",
                    message="",
                    type="end",
                    message_id=str(uuid7()),
                    id=str(uuid7()),
                )
                await websocket.send_json(end_resp.dict())
            except WebSocketDisconnect:
                logging.info("websocket disconnect")
                break
            except Exception as e:
                logging.error(e)
                resp = IChatResponse(
                    message_id="",
                    id="",
                    sender="bot",
                    message="Sorry, something went wrong. Your user limit of api usages has been reached.",
                    type="error",
                )
                await websocket.send_json(resp.dict())
        
        # Remove the live connection from Redis
        await redis_client.delete(key)
        


# Add Routers
app.include_router(api_router_v1, prefix=settings.API_V1_STR)
add_pagination(app)
