from app import crud
from typing import Any
from app.api.deps import get_redis_client
from app.core import security
from app.schemas.user_schema import IUserCreate
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi_pagination import add_pagination
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router as api_router_v1
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware, db
from contextlib import asynccontextmanager
from app.utils.fastapi_globals import GlobalsMiddleware
from app.core.config import settings
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python import get_all_cors_headers
from jose import jwt
from supertokens_python import init, InputAppInfo, SupertokensConfig
from supertokens_python.recipe import emailpassword, session, dashboard, usermetadata
from supertokens_python.recipe.emailpassword import InputFormField
from supertokens_python.recipe.emailpassword.interfaces import (
    APIInterface,
    APIOptions,
    SignUpPostOkResult,
)
from supertokens_python.recipe.emailpassword.types import FormField
from supertokens_python.recipe.usermetadata.asyncio import update_user_metadata
from supertokens_python.recipe.session.framework.fastapi import verify_session


async def user_id_identifier(request: Request):
    verify_session_fn = verify_session(session_required=False)
    session = await verify_session_fn(request=request)

    if session is not None: 
        user_id = session.get_user_id()
        return user_id + ":" + request.scope["path"]
        
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]

    return request.client.host + ":" + request.scope["path"]


def override_email_password_apis(original_implementation: APIInterface):
    original_sign_up_post = original_implementation.sign_up_post

    def extract_field(lst: list[FormField], field: str):
        for d in lst:
            if d.id == field:
                return d.value
        return None

    async def sign_up_post(
        form_fields: list[FormField],
        api_options: APIOptions,
        user_context: dict[str, Any],
    ):
        # First we call the original implementation of signInPOST.
        response = await original_sign_up_post(form_fields, api_options, user_context)

        # Post sign up response, we check if it was successful
        if isinstance(response, SignUpPostOkResult):
            first_name = extract_field(form_fields, "first_name")
            last_name = extract_field(form_fields, "last_name")
            email = response.user.email
            user_id = response.user.user_id
            
            await update_user_metadata(user_id, {
                "first_name": first_name,
                "last_name": last_name
            })
            
            async with db():
                user = IUserCreate(first_name=first_name, last_name=last_name, email=email, id=user_id)
                new_user = await crud.user.create(obj_in=user)
                print("new_user", new_user)

        return response

    original_implementation.sign_up_post = sign_up_post
    return original_implementation


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

app.add_middleware(get_middleware())
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


init(
    app_info=InputAppInfo(
        app_name="clear-docs",
        api_domain="http://localhost:80",
        website_domain="http://localhost:3000",
        api_base_path="/auth",
        website_base_path="/auth",
    ),
    supertokens_config=SupertokensConfig(
        # These are the connection details of the app you created on supertokens.com
        connection_uri=settings.SUPERTOKENS_CORE_URI,
        api_key=settings.SUPERTOKENS_CORE_API_KEY,
    ),
    framework="fastapi",
    recipe_list=[
        session.init(),        
        usermetadata.init(),
        dashboard.init(),
        emailpassword.init(
            sign_up_feature=emailpassword.InputSignUpFeature(
                form_fields=[
                    InputFormField(id="first_name"),
                    InputFormField(id="last_name"),
                ]
            ),
            override=emailpassword.InputOverrideConfig(
                apis=override_email_password_apis
            ),
        ),
    ],  # initializes session features
    # mode="asgi",  # use wsgi if you are running using gunicorn
)

# Set all CORS origins enabled
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        # allow_headers=["*"],
        allow_headers=["Content-Type"] + get_all_cors_headers(),
    )


@app.get("/", dependencies=[Depends(RateLimiter(times=100, hours=24))])
async def root():
    """
    An example "Hello world" FastAPI route.
    """
    return {"message": "Hello World"}


# Add Routers
app.include_router(api_router_v1, prefix=settings.API_V1_STR)
add_pagination(app)
