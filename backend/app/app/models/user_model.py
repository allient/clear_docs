from enum import Enum
from app.models.base_uuid_model import BaseUUIDModel
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime, String
from typing import Optional
from sqlalchemy_utils import ChoiceType
from pydantic import EmailStr
from uuid import UUID

class IGenderEnum(str, Enum):
    female = "female"
    male = "male"
    other = "other"

class UserBase(SQLModel):
    first_name: str
    last_name: str
    email: EmailStr = Field(
        nullable=True, index=True, sa_column_kwargs={"unique": True}
    )
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    birthdate: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )  # birthday with timezone
    role_id: UUID | None = Field(default=None, foreign_key="Role.id")
    phone: str | None
    gender: IGenderEnum | None = Field(
        default=IGenderEnum.other,
        sa_column=Column(ChoiceType(IGenderEnum, impl=String())),
    )
    state: str | None
    country: str | None
    address: str | None


class User(BaseUUIDModel, UserBase, table=True):
    hashed_password: str | None = Field(nullable=False, index=True)
    role: Optional["Role"] = Relationship(  # noqa: F821
        back_populates="users", sa_relationship_kwargs={"lazy": "joined"}
    )
