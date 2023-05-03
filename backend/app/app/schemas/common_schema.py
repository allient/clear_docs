from uuid import UUID
from app.utils.uuid6 import uuid7
from pydantic import BaseModel, validator, EmailStr
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
    id:  str
    message_id: str
    sender: str
    message: str
    type: str
    
    @validator("id", "message_id", pre=True, allow_reuse=True)
    def check_ids(cls, v):        
        if v == "" or v == None:            
            return str(uuid7())
        return v
    
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
    user_id: UUID | None
    message: str

class IDecodedToken(BaseModel):
    """Decoded token schema."""
    user_id: UUID
    username: str|UUID
    email: EmailStr