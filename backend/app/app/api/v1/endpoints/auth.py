from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.deps import authenticate_user
from app.api.deps import get_current_user
from app.models.user_model import User
from app.schemas.user_schema import IUserCreate
from app import crud
from app.schemas.response_schema import IResponseBase
from app.schemas.user_schema import IUserRead
from app.schemas.response_schema import create_response
from aiobotocore.session import get_session
from app.core.config import settings
from aiobotocore.config import AioConfig
from app.api.deps import get_user_id
from app.schemas.common_schema import IDecodedToken


router = APIRouter()


@router.post("/access-token")
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str]:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    response = await authenticate_user(form_data.username, form_data.password)
    return {
        "access_token": response["AccessToken"],
        "token_type": response["TokenType"],
        "refresh_token": response["RefreshToken"],
    }


@router.post("/sign_up")
async def sign_up(
    new_user: IUserCreate,
    decoded_token: IDecodedToken = Depends(get_user_id)
) -> IResponseBase[IUserRead]:
    """
    This Sign up is intended after cognito sign up and requires its id
    """
    new_user.email = decoded_token.email    
    current_user = await crud.user.get_by_email(email=new_user.email)
    if current_user != None:
        raise HTTPException(status_code=400, detail=f"This user already exists")
    
    current_user = await crud.user.create(obj_in=new_user)
    return create_response(data=current_user)
