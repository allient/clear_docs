import os
import requests
from app.auth.auth_schema import JWKS
from app.core.config import settings


jwks = JWKS.parse_obj(
    requests.get(
        f"{settings.COGNITO_URL}/{settings.COGNITO_POOL_ID}/.well-known/jwks.json"
    ).json()
)
