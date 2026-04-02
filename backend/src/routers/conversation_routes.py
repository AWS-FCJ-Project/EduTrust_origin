from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from src.auth.dependencies import get_current_user
from src.conversation.conversation_handler import ConversationHandler
from src.schemas.conversation_schema import (
    ConversationResponseSchema,
    ConversationSummarySchema,
)

router = APIRouter(prefix="/unified-agent", tags=["Conversations"])


def get_conversation_handler(request: Request) -> ConversationHandler:
    return request.app.state.conversation_handler


@router.post("/conversations", response_model=ConversationResponseSchema)
def create_conversation(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ConversationHandler, Depends(get_conversation_handler)],
):
    conversation_id = str(uuid4())
    conversation = handler.create_conversation(
        conversation_id, user_id=str(current_user["_id"])
    )
    return ConversationResponseSchema(
        conversation_id=conversation_id,
        title=conversation.get("title", "New Chat"),
        created_at=conversation.get("created_at"),
        updated_at=conversation.get("updated_at"),
        messages=[],
    )


@router.get("/conversations", response_model=list[ConversationSummarySchema])
def list_conversations(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ConversationHandler, Depends(get_conversation_handler)],
    limit: int = 50,
):
    return handler.list_conversations(user_id=str(current_user["_id"]), limit=limit)


@router.get("/conversations/latest", response_model=ConversationResponseSchema)
def get_latest_conversation(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ConversationHandler, Depends(get_conversation_handler)],
    message_limit: int = 50,
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
def get_conversation(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ConversationHandler, Depends(get_conversation_handler)],
    message_limit: int = 0,
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
def delete_conversation(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ConversationHandler, Depends(get_conversation_handler)],
) -> Response:
    deleted = handler.delete_conversation(
        conversation_id, user_id=str(current_user["_id"])
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
