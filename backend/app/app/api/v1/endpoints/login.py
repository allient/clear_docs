from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.utils.helpers import Helper
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session


router = APIRouter()


@router.post("/access-token")
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str]:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    secret_hash = Helper.get_secret_hash(
        form_data.username, settings.COGNITO_CLIENT_ID, settings.COGNITO_CLIENT_SECRET
    )

    async def authenticate_user(username: str, password: str):
        session = get_session()
        async with session.create_client(
            "cognito-idp",
            region_name=settings.COGNITO_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=AioConfig(max_pool_connections=128),
        ) as client:
            try:
                auth_response = await client.admin_initiate_auth(
                    UserPoolId=settings.COGNITO_POOL_ID,
                    ClientId=settings.COGNITO_CLIENT_ID,
                    AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                    AuthParameters={
                        "USERNAME": username,
                        "PASSWORD": password,
                        "SECRET_HASH": secret_hash,
                    },
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"{e}")

            if "ChallengeName" in auth_response and auth_response["ChallengeName"] == "NEW_PASSWORD_REQUIRED":
                # Respond to the NEW_PASSWORD_REQUIRED challenge
                try:
                    challenge_response = await client.admin_respond_to_auth_challenge(
                        UserPoolId=settings.COGNITO_POOL_ID,
                        ClientId=settings.COGNITO_CLIENT_ID,
                        ChallengeName="NEW_PASSWORD_REQUIRED",
                        ChallengeResponses={
                            "USERNAME": username,
                            "NEW_PASSWORD": password,
                            "SECRET_HASH": secret_hash,
                        },
                        Session=auth_response["Session"],
                    )
                except Exception as e:                    
                    raise HTTPException(status_code=400, detail=f"Error responding to challenge: {e}")
                    # Handle the error appropriately (e.g., retry the request, log the error, etc.)
                else:
                    print("challenge_response", challenge_response)
                    access_token = challenge_response["AuthenticationResult"]
                    return access_token
            else:
                # The access token is returned in the AuthenticationResult
                try:
                    access_token = auth_response["AuthenticationResult"]
                    return access_token
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Error authenticating: {e}")

    return await authenticate_user(form_data.username, form_data.password)
