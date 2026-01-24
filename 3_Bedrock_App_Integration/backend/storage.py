"""
In-memory conversation store with a process-wide lock for thread safety.

Conversation dict shape: conversation_id, user_id, created_at, updated_at,
messages (list of ChatMessage), model_id, temperature, max_tokens,
total_tokens, message_count, has_multimodal, file_count.

- conversations, conversations_lock: module-level store and lock.
- _get_conversation_or_404: return conv or raise 404.
- _verify_user_ownership: raise 403 if conversation["user_id"] != user_id.
- _get_all_conversations: snapshot of all convs (caller must hold or not care about mutability).
- _build_conversation_response, _build_conversation_summary: conv dict -> Pydantic.

Data is lost on process restart. For production, replace with a DB or Redis.
"""
import threading
from typing import List

from fastapi import HTTPException

from models import ConversationResponse, ConversationSummary

# Global store: id -> conversation dict. Lock guards all reads/writes.
conversations: dict[str, dict] = {}
conversations_lock = threading.Lock()


def _get_conversation_or_404(conversation_id: str) -> dict:
    """Return the conversation dict for conversation_id, or raise 404."""
    conversation = conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conversation_id}' not found",
        )
    return conversation


def _verify_user_ownership(conversation: dict, user_id: str) -> None:
    """Raise 403 if conversation["user_id"] != user_id."""
    if conversation.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this conversation",
        )


def _get_all_conversations() -> List[dict]:
    """Return a list of all conversation dicts. conversations_lock is held during the copy."""
    with conversations_lock:
        return list(conversations.values())


def _build_conversation_response(conversation: dict) -> ConversationResponse:
    """Map a conversation dict to ConversationResponse; uses .get() with defaults for optional fields."""
    return ConversationResponse(
        conversation_id=conversation["conversation_id"],
        user_id=conversation["user_id"],
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
        messages=conversation["messages"],
        model_id=conversation["model_id"],
        temperature=conversation["temperature"],
        max_tokens=conversation["max_tokens"],
        total_tokens=conversation.get("total_tokens", 0),
        message_count=conversation.get("message_count", 0),
        has_multimodal=conversation.get("has_multimodal", False),
        file_count=conversation.get("file_count", 0)
    )


def _build_conversation_summary(conversation: dict) -> ConversationSummary:
    """Map a conversation dict to ConversationSummary for list endpoints."""
    return ConversationSummary(
        conversation_id=conversation["conversation_id"],
        user_id=conversation["user_id"],
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
        message_count=conversation.get("message_count", 0),
        total_tokens=conversation.get("total_tokens", 0),
        model_id=conversation["model_id"],
        has_multimodal=conversation.get("has_multimodal", False),
        file_count=conversation.get("file_count", 0)
    )
