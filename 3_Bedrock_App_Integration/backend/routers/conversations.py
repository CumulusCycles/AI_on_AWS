"""
User-scoped conversation CRUD. All routes (except create) require user_id to match
the conversation owner; 403 otherwise.

- POST /conversations: create empty conversation; optional model_id, temperature, max_tokens.
- GET /conversations?user_id=: list that user's conversations, newest first.
- GET /conversations/:id?user_id=: get one; 404 if missing, 403 if not owner.
- DELETE /conversations/:id?user_id=: delete one; 403 if not owner.
"""
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter

from config import DEFAULT_MAX_TOKENS, DEFAULT_MODEL_ID, DEFAULT_TEMPERATURE
from models import ConversationCreateRequest, ConversationResponse, ConversationSummary
from storage import (
    _build_conversation_response,
    _build_conversation_summary,
    _get_conversation_or_404,
    _verify_user_ownership,
    conversations,
    conversations_lock,
)

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreateRequest) -> ConversationResponse:
    """Create an empty conversation. Returns conversation_id for use in POST /chat (conversation_id)."""
    conversation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    conversation = {
        "conversation_id": conversation_id,
        "user_id": request.user_id,
        "created_at": now,
        "updated_at": now,
        "messages": [],
        "model_id": request.model_id or DEFAULT_MODEL_ID,
        "temperature": request.temperature if request.temperature is not None else DEFAULT_TEMPERATURE,
        "max_tokens": request.max_tokens if request.max_tokens is not None else DEFAULT_MAX_TOKENS,
        "total_tokens": 0,
        "message_count": 0,
        "has_multimodal": False,
        "file_count": 0
    }
    
    with conversations_lock:
        conversations[conversation_id] = conversation

    return _build_conversation_response(conversation)


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(user_id: str) -> List[ConversationSummary]:
    """List conversations whose user_id matches. Sorted by updated_at descending."""
    with conversations_lock:
        user_conversations = [c for c in conversations.values() if c.get("user_id") == user_id]
    user_conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    return [_build_conversation_summary(conv) for conv in user_conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, user_id: str) -> ConversationResponse:
    """Return full conversation. 404 if not found, 403 if user_id is not the owner."""
    with conversations_lock:
        conversation = _get_conversation_or_404(conversation_id)
        _verify_user_ownership(conversation, user_id)
    
    return _build_conversation_response(conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str) -> dict:
    """Delete the conversation. 404 if not found, 403 if user_id is not the owner."""
    with conversations_lock:
        conversation = _get_conversation_or_404(conversation_id)
        _verify_user_ownership(conversation, user_id)
        del conversations[conversation_id]
    
    return {"message": f"Conversation '{conversation_id}' deleted successfully"}
