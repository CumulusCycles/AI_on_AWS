"""
Pydantic request/response models for the Bedrock App Integration API.

- ContentBlock, ChatMessage: Converse API–style content (text and/or image).
- ChatResponse: /chat response (message, model_id, usage, conversation_id).
- ConversationCreateRequest, ConversationResponse, ConversationSummary:
  conversation CRUD and storage shape.
- AnalyticsResponse, TimelineDataPoint, TimelineResponse: /admin/analytics.
- ModelUsageStats, ModelsResponse: /admin/models.
- SystemInfoResponse: /admin/system.

ConfigDict(protected_namespaces=()) allows Pydantic v2 to use 'model_'
as a field name in model_id, model_config, etc.
"""
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from config import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


class ContentBlock(BaseModel):
    """One block of content: text or image. For images, image={"format": "jpeg"|"png"|"gif"|"webp", "source": {"bytes": raw_bytes}}."""

    text: Optional[str] = None
    image: Optional[dict] = None


class ChatMessage(BaseModel):
    """Single message in a conversation. content is plain text or a list of ContentBlocks (multimodal)."""

    role: Literal["user", "assistant"] = Field(..., description="'user' or 'assistant'")
    content: Union[str, List[ContentBlock]] = Field(
        ...,
        description="Plain string or list of ContentBlocks (text + images)",
    )

    @classmethod
    def from_text(cls, role: str, text: str) -> "ChatMessage":
        """Build a text-only message; used for assistant replies."""
        return cls(role=role, content=text)

    @classmethod
    def from_multimodal(cls, role: str, content_blocks: List[ContentBlock]) -> "ChatMessage":
        """Build a message with text and/or image blocks; used for user input with photos."""
        return cls(role=role, content=content_blocks)


class ChatResponse(BaseModel):
    """Response from POST /chat. conversation_id is set when a new or existing conversation is used."""

    model_config = ConfigDict(protected_namespaces=())

    message: str
    model_id: str
    usage: Optional[dict] = None  # input_tokens, output_tokens, total_tokens
    conversation_id: Optional[str] = None


class ConversationCreateRequest(BaseModel):
    """Body for POST /conversations. Creates an empty conversation with optional model/temperature/max_tokens."""

    model_config = ConfigDict(protected_namespaces=())

    user_id: str = Field(..., description="Owner of the conversation")
    model_id: Optional[str] = None
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS


class ConversationResponse(BaseModel):
    """Full conversation as returned by GET /conversations/:id and /admin/conversations/:id."""

    model_config = ConfigDict(protected_namespaces=())

    conversation_id: str
    user_id: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage]
    model_id: str
    temperature: float
    max_tokens: int
    total_tokens: int
    message_count: int
    has_multimodal: bool
    file_count: int


class ConversationSummary(BaseModel):
    """Reduced fields for list endpoints: GET /conversations, /admin/conversations, /admin/activity/recent."""

    model_config = ConfigDict(protected_namespaces=())
    
    conversation_id: str
    user_id: str
    created_at: str
    updated_at: str
    message_count: int
    total_tokens: int
    model_id: str
    has_multimodal: bool
    file_count: int


class AnalyticsResponse(BaseModel):
    """Response for GET /admin/analytics: aggregated counts and averages."""

    total_conversations: int
    total_messages: int
    total_tokens: int
    average_tokens_per_conversation: float
    average_messages_per_conversation: float
    conversations_with_multimodal: int
    total_files_uploaded: int
    most_used_model: Optional[str] = None


class TimelineDataPoint(BaseModel):
    """One day in GET /admin/analytics/timeline."""

    date: str  # ISO date
    conversations: int
    messages: int
    tokens: int


class TimelineResponse(BaseModel):
    """Response for GET /admin/analytics/timeline."""

    timeline: List[TimelineDataPoint]


class ModelUsageStats(BaseModel):
    """Per-model stats in GET /admin/models."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    conversation_count: int
    total_tokens: int
    average_tokens_per_conversation: float


class ModelsResponse(BaseModel):
    """Response for GET /admin/models."""

    models: List[ModelUsageStats]


class SystemInfoResponse(BaseModel):
    """Response for GET /admin/system: totals and default config."""

    model_config = ConfigDict(protected_namespaces=())

    total_conversations: int
    total_messages: int
    total_tokens: int
    default_model_id: str
    default_temperature: float
    default_max_tokens: int
