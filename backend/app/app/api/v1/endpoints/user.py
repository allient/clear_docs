from app import crud
from app.deps import user_deps
from app.models.user_model import User
from fastapi import (
    APIRouter,
    Depends,
)
from app.schemas.response_schema import (
    IGetResponseBase,
    IGetResponsePaginated,
    create_response,
)
from app.schemas.user_schema import (
    IUserRead,
)
from fastapi_pagination import Params

from app.auth.deps import get_auth
from app.auth.auth_schema import JWTAuthorizationCredentials
from app.api.deps import get_current_user

router = APIRouter()


@router.get("")
async def get_my_data(
    current_user: User = Depends(get_current_user),
) -> IGetResponseBase[IUserRead]:
    """
    Gets my user profile information
    """
    return create_response(data=current_user)
