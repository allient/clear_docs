from app.utils.partial import optional
from uuid import UUID
from enum import Enum

from app.models.user_model import UserBase
from app.models.user_model import IRoleEnum


class IUserCreate(UserBase):
    id: UUID


# All these fields are optional
@optional
class IUserUpdate(UserBase):
    pass


class IUserRead(UserBase):
    id: UUID
    role: IRoleEnum


class IUserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
