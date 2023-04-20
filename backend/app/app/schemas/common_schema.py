from uuid import UUID
from pydantic import BaseModel, validator
from enum import Enum


class IMetaGeneral(BaseModel):
    pass


class IOrderEnum(str, Enum):
    ascendent = "ascendent"
    descendent = "descendent"


class TokenType(str, Enum):
    ACCESS = "access_token"
    REFRESH = "refresh_token"


class IMessage(BaseModel):
    role: str
    content: str


class IChoice(BaseModel):
    index: int
    message: IMessage
    finish_reason: str


class IUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class IChatCompletionResponse(BaseModel):
    created: int
    choices: list[IChoice]
    usage: IUsage
    id: str
    object: str

class IChatResponse(BaseModel):
    """Chat response schema."""

    sender: str
    message: str
    type: str

    @validator("sender")
    def sender_must_be_bot_or_you(cls, v):
        if v not in ["bot", "you"]:
            raise ValueError("sender must be bot or you")
        return v

    @validator("type")
    def validate_message_type(cls, v):
        if v not in ["start", "stream", "end", "error", "info"]:
            raise ValueError("type must be start, stream or end")
        return v

class IUserMessage(BaseModel):
    """User message schema."""
    user_id: UUID
    message: str
