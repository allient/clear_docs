from app.utils.partial import optional
from uuid import UUID
from enum import Enum

from app.models.user_model import UserBase


class IUserCreate(UserBase):
    id: UUID


# All these fields are optional
@optional
class IUserUpdate(UserBase):
    pass


class IUserRead(UserBase):
    id: UUID


class IUserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
