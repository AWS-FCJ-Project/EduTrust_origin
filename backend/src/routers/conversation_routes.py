from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from src.auth.dependencies import get_current_user
from src.schemas.conversation_schema import (
    ConversationResponseSchema,
    ConversationSummarySchema,
)
from src.state import get_conversation_handler

router = APIRouter(prefix="/unified-agent", tags=["Conversations"])


@router.post("/conversations", response_model=ConversationResponseSchema)
async def create_conversation(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler=Depends(get_conversation_handler),
):
    conversation_id = str(uuid4())
    user_id = str(current_user["_id"])
    conversation = handler.create_conversation(conversation_id, user_id=user_id)
    return ConversationResponseSchema(
        conversation_id=conversation_id,
        title=conversation.get("title", "New Chat"),
        created_at=conversation.get("created_at"),
        updated_at=conversation.get("updated_at"),
        messages=[],
    )


@router.get("/conversations", response_model=list[ConversationSummarySchema])
async def list_conversations(
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = 50,
    query: str | None = None,
    handler=Depends(get_conversation_handler),
):
    user_id = str(current_user["_id"])
    if query and query.strip():
        return handler.search_conversations(user_id=user_id, query=query, limit=limit)
    return handler.list_conversations(user_id=user_id, limit=limit)


@router.get("/conversations/latest", response_model=ConversationResponseSchema)
async def get_latest_conversation(
    current_user: Annotated[dict, Depends(get_current_user)],
    message_limit: int = 50,
    handler=Depends(get_conversation_handler),
):
    user_id = str(current_user["_id"])
    conversation_id = handler.get_latest_conversation_id(user_id)
    if not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No conversation found"
        )

    conversation = handler.get_conversation(conversation_id, user_id=user_id)
    messages = handler.get_context(
        conversation_id, message_limit=message_limit, user_id=user_id
    )
    return ConversationResponseSchema(
        conversation_id=conversation_id,
        title=conversation.get("title", "New Chat") if conversation else "New Chat",
        created_at=conversation.get("created_at") if conversation else None,
        updated_at=conversation.get("updated_at") if conversation else None,
        messages=messages,
    )


@router.get(
    "/conversations/{conversation_id}", response_model=ConversationResponseSchema
)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    message_limit: int = 0,
    handler=Depends(get_conversation_handler),
):
    user_id = str(current_user["_id"])
    conversation = handler.get_conversation(conversation_id, user_id=user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    messages = handler.get_context(
        conversation_id, message_limit=message_limit, user_id=user_id
    )
    return ConversationResponseSchema(
        conversation_id=conversation_id,
        title=conversation.get("title", "New Chat"),
        created_at=conversation.get("created_at"),
        updated_at=conversation.get("updated_at"),
        messages=messages,
    )


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler=Depends(get_conversation_handler),
) -> Response:
    user_id = str(current_user["_id"])
    deleted = handler.delete_conversation(conversation_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
