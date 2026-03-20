from backend.src.memory.conversation_handler import ConversationHandler

conversation_handler: ConversationHandler | None = None


def get_conversation_handler() -> ConversationHandler:
    if conversation_handler is None:
        raise RuntimeError("ConversationHandler not initialized")
    return conversation_handler
