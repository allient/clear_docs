from pydantic import BaseModel
from enum import Enum
from app.schemas.role_schema import IRoleRead


class IMetaGeneral(BaseModel):
    roles: list[IRoleRead]


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