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
    current_user = await crud.user.get(id=decoded_token.user_id)
    if current_user != None:
        raise HTTPException(status_code=400, detail=f"This user already exists")

    session = get_session()
    async with session.create_client(
        "cognito-idp",
        region_name=settings.COGNITO_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=AioConfig(max_pool_connections=128),
    ) as client:
        try:
            auth_response = await client.admin_get_user(
                UserPoolId=settings.COGNITO_POOL_ID,
                Username=str(decoded_token.username),
            )
            email = next(
                (
                    attr["Value"]
                    for attr in auth_response["UserAttributes"]
                    if attr["Name"] == "email"
                ),
                None,
            )
            new_user.email = email
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    current_user = await crud.user.create(obj_in=new_user)
    return create_response(data=current_user)
