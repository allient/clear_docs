from typing import Optional
from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk, JWTError
from jose.utils import base64url_decode
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from app.auth.auth_schema import JWKS, JWTAuthorizationCredentials
from app.core.config import settings
import boto3


class JWTBearer(HTTPBearer):
    def __init__(self, jwks: JWKS, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.cognito = boto3.client(
            'cognito-idp', region_name=settings.COGNITO_REGION)
        self.kid_to_jwk = {jwk["kid"]: jwk for jwk in jwks.keys}

    def verify_jwk_token(self, jwt_credentials: JWTAuthorizationCredentials) -> bool:
        try:
            public_key = self.kid_to_jwk[jwt_credentials.header["kid"]]
        except KeyError:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="JWK public key not found"
            )

        key = jwk.construct(public_key)
        decoded_signature = base64url_decode(
            jwt_credentials.signature.encode())

        return key.verify(jwt_credentials.message.encode(), decoded_signature)

    async def __call__(self, request: Request) -> Optional[JWTAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Wrong authentication method"
                )

            jwt_token = credentials.credentials
            message, signature = jwt_token.rsplit(".", 1)

            try:
                jwt_credentials = JWTAuthorizationCredentials(
                    jwt_token=jwt_token,
                    header=jwt.get_unverified_header(jwt_token),
                    claims=jwt.get_unverified_claims(jwt_token),
                    signature=signature,
                    message=message,
                )

                try:
                    # validate if the user is still allowed to login.
                    # If disabled or deleted from cognito tokens are still valid
                    # for some time.
                    response = self.cognito.get_user(
                        AccessToken=jwt_token
                    )
                    print("response: ", response)
                except self.cognito.exceptions.NotAuthorizedException as e:
                    print(f"Error in get_user: {e.__str__()}")
                    raise HTTPException(
                        status_code=HTTP_403_FORBIDDEN, detail="Access Token has expired")

            except JWTError:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="JWK invalid")

            if not self.verify_jwk_token(jwt_credentials):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="JWK invalid")

            return jwt_credentials