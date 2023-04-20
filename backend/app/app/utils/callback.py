"""Callback handlers used in the app."""
from typing import Any, Dict, List
from app.schemas.common_schema import IChatResponse
from app.utils.uuid6 import uuid7
from langchain.callbacks.base import AsyncCallbackHandler


class StreamingLLMCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming LLM responses."""

    def __init__(self, websocket):
        self.websocket = websocket
        self.message_id = str(uuid7())

    def update_message_id(self):
        self.message_id = str(uuid7())

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        resp = IChatResponse(sender="bot", message=token, type="stream", message_id=self.message_id, id="")
        await self.websocket.send_json(resp.dict())


class QuestionGenCallbackHandler(AsyncCallbackHandler):
    """Callback handler for question generation."""

    def __init__(self, websocket):
        self.websocket = websocket
        self.message_id = str(uuid7())

    def update_message_id(self):
        self.message_id = str(uuid7())

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        resp = IChatResponse(
            sender="bot", message="Synthesizing question...", type="info", message_id=str(uuid7()), id=str(uuid7())
        )
        await self.websocket.send_json(resp.dict())