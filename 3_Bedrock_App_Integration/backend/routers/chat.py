"""
POST /chat: damage assessment and follow-up via AWS Bedrock Converse API.

Accepts two content types:
- multipart/form-data: user_id, message, optional conversation_id, and optional
  model_id/temperature/max_tokens. For initial submission (no conversation_id),
  exactly 3 image files are required (wide-angle, straight-on, closeup). For
  follow-up (with conversation_id), files are optional.
- application/json: user_id, conversation_id (required), message; no files.
  Used for text-only follow-ups.

Flow: build user message (text + optional images) -> if conversation_id, load
history and append, else messages=[user_message]. Call converse() with
SYSTEM_PROMPT. Persist assistant reply and return ChatResponse with
conversation_id (new or existing). On initial submission without
conversation_id, a new conversation is created and its id returned.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Request

from config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL_ID,
    DEFAULT_TEMPERATURE,
    SYSTEM_PROMPT,
    bedrock_client,
)
from models import ChatMessage, ChatResponse, ContentBlock
from storage import (
    _get_conversation_or_404,
    _verify_user_ownership,
    conversations,
    conversations_lock,
)
from utils import format_message_for_converse, process_uploaded_file

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_float(v: str | None) -> Optional[float]:
    """Parse form/JSON string to float; return None for empty or invalid."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_int(v: str | None) -> Optional[int]:
    """Parse form/JSON string to int; return None for empty or invalid."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request) -> ChatResponse:
    """
    Handle damage assessment (initial or follow-up). Dispatches on Content-Type:
    multipart (initial or follow-up with optional files) vs JSON (follow-up, no files).
    """
    ct = (request.headers.get("content-type") or "").lower()

    if "multipart/form-data" in ct:
        form = await request.form()
        user_id = str(form.get("user_id") or "").strip() or None
        if not user_id:
            raise HTTPException(400, "user_id is required")
        message = str(form.get("message") or "").strip() or None
        if not message:
            raise HTTPException(400, "message is required")
        raw_cid = form.get("conversation_id")
        conversation_id = str(raw_cid).strip() if (raw_cid and str(raw_cid).strip()) else None
        model_id = str(form.get("model_id") or "").strip() or None
        temperature = _parse_float(form.get("temperature"))
        max_tokens = _parse_int(form.get("max_tokens"))
        # Collect file-like entries from form (key "files" can have multiple)
        raw = form.getlist("files") if hasattr(form, "getlist") else []
        file_list = [f for f in (raw if isinstance(raw, list) else [raw] if raw else []) if hasattr(f, "file")]
    elif "application/json" in ct:
        body = await request.json()
        user_id = str(body.get("user_id") or "").strip()
        message = str(body.get("message") or "").strip()
        conversation_id = str(body.get("conversation_id") or "").strip() or None
        if not user_id or not message:
            raise HTTPException(400, "user_id and message are required")
        if not conversation_id:
            raise HTTPException(
                400,
                "conversation_id is required for follow-up. Initial submission with images must use multipart/form-data (not application/json) with exactly 3 image files.",
            )
        model_id = str(body.get("model_id") or "").strip() or None
        temperature = _parse_float(body.get("temperature"))
        max_tokens = _parse_int(body.get("max_tokens"))
        file_list = []
    else:
        raise HTTPException(
            400,
            "Content-Type must be multipart/form-data (initial) or application/json (follow-up)",
        )

    is_initial_submission = conversation_id is None
    if is_initial_submission and len(file_list) != 3:
        raise HTTPException(
            status_code=400,
            detail="Initial damage assessment requires exactly 3 images: wide-angle, straight-on, and closeup. Please upload exactly 3 vehicle damage photos.",
        )

    logger.info(
        "Chat request: user_id=%r conversation_id=%r is_initial=%s files=%d",
        user_id,
        conversation_id,
        is_initial_submission,
        len(file_list),
    )

    # Build content: [text] + [image ContentBlocks] from uploaded files
    content_blocks = [ContentBlock(text=message.strip())]
    for file in file_list:
        try:
            content_blocks.append(process_uploaded_file(file))
        finally:
            file.file.close()

    user_message = ChatMessage.from_multimodal("user", content_blocks)

    if conversation_id:
        # Follow-up: append to existing conversation; use conv's model/temp/max_tokens if not overridden
        with conversations_lock:
            conversation = _get_conversation_or_404(conversation_id)
            _verify_user_ownership(conversation, user_id)
            
            # Get settings (use form overrides if provided, otherwise use conversation defaults)
            model_id = model_id or conversation.get('model_id', DEFAULT_MODEL_ID)
            temperature = temperature if temperature is not None else conversation.get('temperature', DEFAULT_TEMPERATURE)
            max_tokens = max_tokens if max_tokens is not None else conversation.get('max_tokens', DEFAULT_MAX_TOKENS)
            
            messages = conversation["messages"].copy()
            messages.append(user_message)
            # Persist user message now; assistant message is appended after converse() returns
            conversation["messages"].append(user_message)
            conversation['message_count'] = conversation.get('message_count', 0) + 1
            conversation['updated_at'] = datetime.utcnow().isoformat()
            conversation['has_multimodal'] = conversation.get('has_multimodal', False) or len(file_list) > 0
            conversation['file_count'] = conversation.get('file_count', 0) + len(file_list)
    else:
        # Initial: no history; single user message. conversation_id remains None until we create one
        messages = [user_message]
        model_id = model_id or DEFAULT_MODEL_ID
        temperature = temperature or DEFAULT_TEMPERATURE
        max_tokens = max_tokens or DEFAULT_MAX_TOKENS
        conversation_id = None
    
    try:
        # Format messages for Converse API
        formatted_messages = [format_message_for_converse(msg) for msg in messages]
        
        # Prepare inference configuration
        inference_config = {
            "maxTokens": max_tokens,
            "temperature": temperature
        }
        
        # Prepare system prompt for automobile damage assessment
        # Include system prompt to define the assistant's role and behavior
        system_prompt = [{"text": SYSTEM_PROMPT}]
        
        # Call Converse API with system prompt
        response = bedrock_client.converse(
            modelId=model_id,
            messages=formatted_messages,
            system=system_prompt,
            inferenceConfig=inference_config
        )
        
        # Extract the assistant's message from Converse API response
        assistant_message = ""
        output_message = response.get('output', {}).get('message', {})
        if output_message.get('content'):
            for content_block in output_message['content']:
                if content_block.get('text'):
                    assistant_message += content_block['text']
        
        # Extract usage information from Converse API response
        usage = None
        if 'usage' in response:
            usage_info = response['usage']
            usage = {
                "input_tokens": usage_info.get('inputTokens', 0),
                "output_tokens": usage_info.get('outputTokens', 0),
                "total_tokens": usage_info.get('totalTokens', 0)
            }

        logger.debug("Bedrock response received: usage=%s", usage)

        # If using conversation mode, save the assistant's response and update metrics
        if conversation_id:
            with conversations_lock:
                conversation = conversations[conversation_id]
                conversation['messages'].append(ChatMessage.from_text("assistant", assistant_message))
                conversation['message_count'] = conversation.get('message_count', 0) + 1
                conversation['updated_at'] = datetime.utcnow().isoformat()
                if usage:
                    conversation['total_tokens'] = conversation.get('total_tokens', 0) + usage.get('total_tokens', 0)
        else:
            # Initial submission: create a new conversation and return its id for follow-ups
            new_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            with conversations_lock:
                conversations[new_id] = {
                    "conversation_id": new_id,
                    "user_id": user_id,
                    "created_at": now,
                    "updated_at": now,
                    "messages": [user_message, ChatMessage.from_text("assistant", assistant_message)],
                    "model_id": model_id,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "total_tokens": usage.get("total_tokens", 0) if usage else 0,
                    "message_count": 2,
                    "has_multimodal": len(file_list) > 0,
                    "file_count": len(file_list),
                }
            conversation_id = new_id

        return ChatResponse(
            message=assistant_message,
            model_id=model_id,
            usage=usage,
            conversation_id=conversation_id
        )
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise HTTPException(
            status_code=500,
            detail=f"AWS Bedrock error ({error_code}): {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
