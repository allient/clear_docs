import requests
from app.auth.JWTBearer import JWTBearer
from app.auth.auth_schema import JWKS
from app.core.config import settings


def get_auth():
    jwks = JWKS.parse_obj(
        requests.get(
            f"{settings.COGNITO_URL}/{settings.COGNITO_POOL_ID}/.well-known/jwks.json"
        ).json()
    )
    return JWTBearer(jwks)