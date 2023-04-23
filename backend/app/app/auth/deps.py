import requests
from app.auth.JWTBearer import JWTBearer
from app.auth.auth_schema import JWKS
from app.core.config import settings
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.config import settings
from app.utils.helpers import Helper
from app.models.user_model import User


def get_auth():
    jwks = JWKS.parse_obj(
        requests.get(
            f"{settings.COGNITO_URL}/{settings.COGNITO_POOL_ID}/.well-known/jwks.json"
        ).json()
    )
    return JWTBearer(jwks)


async def authenticate_user(username: str, password: str):
    secret_hash = Helper.get_secret_hash(
        username, settings.COGNITO_CLIENT_ID, settings.COGNITO_CLIENT_SECRET
    )
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

        if (
            "ChallengeName" in auth_response
            and auth_response["ChallengeName"] == "NEW_PASSWORD_REQUIRED"
        ):
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
                raise HTTPException(
                    status_code=400, detail=f"Error responding to challenge: {e}"
                )
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
                raise HTTPException(
                    status_code=400, detail=f"Error authenticating: {e}"
                )



