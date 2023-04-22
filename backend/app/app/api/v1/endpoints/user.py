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

router = APIRouter()


@router.get("/list")
async def read_users_list(
    params: Params = Depends(),    
) -> IGetResponsePaginated[IUserRead]:
    """
    Retrieve users. Requires admin or manager role

    Required roles:
    - admin
    - manager
    """
    users = await crud.user.get_multi_paginated(params=params)
    return create_response(data=users)


@router.get("/{user_id}")
async def get_user_by_id(
    user: User = Depends(user_deps.is_valid_user),
) -> IGetResponseBase[IUserRead]:
    """
    Gets a user by his/her id

    Required roles:
    - admin
    - manager
    """
    return create_response(data=user)


# @router.get("")
# async def get_my_data(
#     current_user: User = Depends(deps.get_current_user()),
# ) -> IGetResponseBase[IUserRead]:
#     """
#     Gets my user profile information
#     """
#     return create_response(data=current_user)
