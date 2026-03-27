from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from src.auth.dependencies import get_current_user
from src.schemas.conversation_schema import ConversationResponseSchema
from src.state import get_conversation_handler

router = APIRouter(prefix="/unified-agent", tags=["Conversations"])


@router.post("/conversations", response_model=ConversationResponseSchema)
async def create_conversation(
    email: Annotated[str, Depends(get_current_user)],
    handler=Depends(get_conversation_handler),
):
    conversation_id = str(uuid4())
    handler.touch_conversation(conversation_id, user_id=email)
    return ConversationResponseSchema(conversation_id=conversation_id, messages=[])


@router.get("/conversations/latest", response_model=ConversationResponseSchema)
async def get_latest_conversation(
    email: Annotated[str, Depends(get_current_user)],
    message_limit: int = 50,
    handler=Depends(get_conversation_handler),
):
    conversation_id = handler.get_latest_conversation_id(email)
    if not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No conversation found"
        )
    messages = handler.get_context(
        conversation_id, message_limit=message_limit, user_id=email
    )
    return ConversationResponseSchema(
        conversation_id=conversation_id, messages=messages
    )


@router.get(
    "/conversations/{conversation_id}", response_model=ConversationResponseSchema
)
async def get_conversation(
    conversation_id: str,
    email: Annotated[str, Depends(get_current_user)],
    message_limit: int = 0,
    handler=Depends(get_conversation_handler),
):
    messages = handler.get_context(
        conversation_id, message_limit=message_limit, user_id=email
    )
    if not messages and not handler.conversation_exists(conversation_id, user_id=email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return ConversationResponseSchema(
        conversation_id=conversation_id, messages=messages
    )
