from enum import Enum
from app.models.base_uuid_model import BaseUUIDModel
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime, String
from typing import Optional
from sqlalchemy_utils import ChoiceType
from pydantic import EmailStr
from uuid import UUID


class UserBase(SQLModel):
    first_name: str
    last_name: str
    email: EmailStr = Field(
        nullable=True, index=True, sa_column_kwargs={"unique": True}
    )
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class User(BaseUUIDModel, UserBase, table=True):
    pass
