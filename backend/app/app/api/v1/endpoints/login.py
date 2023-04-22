from datetime import timedelta
from app.schemas.user_schema import IUserCreate
from fastapi import APIRouter, Body, Depends, HTTPException, Response
import httpx
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import EmailStr
from pydantic import ValidationError
from app import crud
from app.api import deps
from app.core import security
from app.core.config import settings
from app.schemas.common_schema import TokenType, IMetaGeneral
from app.schemas.token_schema import TokenRead, Token, RefreshToken
from app.schemas.response_schema import IPostResponseBase, create_response
from supertokens_python.recipe.emailpassword.asyncio import sign_up
from supertokens_python.recipe.emailpassword.interfaces import (
    SignUpEmailAlreadyExistsError,
)
from fastapi_limiter.depends import RateLimiter


router = APIRouter()

@router.post("/access-token")
async def login_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str]:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    payload = {
        "formFields": [
            {"id": "email", "value": form_data.username},
            {"id": "password", "value": form_data.password},
        ]
    }
    async with httpx.AsyncClient() as client:
        output = await client.post("http://localhost:8000/auth/signin", json=payload)
        front_token = output.headers.get("front-token")
        st_access_token = output.headers.get("st-access-token")
        st_refresh_token = output.headers.get("st-refresh-token")
        result = output.json()

    if "user" not in result:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    user = result["user"]
    # Set the session token as a cookie in the response
    response.set_cookie("sFrontToken", front_token)
    response.set_cookie("sRefreshToken", st_refresh_token)
    response.set_cookie("sAccessToken", st_access_token)

    return {"message": f"User {user['id']} logged in successfully"}
