"""
Admin-only routes (no user_id checks; full access to all conversations).

- GET /admin/analytics: aggregated counts and averages.
- GET /admin/analytics/timeline?days=: daily conversation/message/token counts.
- GET /admin/conversations?sort_by=&order=: list all; sort_by in created_at|updated_at|message_count|total_tokens.
- GET /admin/conversations/:id: full conversation.
- GET /admin/conversations/:id/stats: alias for above.
- DELETE /admin/conversations/:id: delete one.
- POST /admin/conversations/bulk-delete: body ["id1","id2"]; returns deleted_count, not_found.
- GET /admin/models: per-model usage (conversation count, tokens, averages).
- GET /admin/system: totals and default model/temperature/max_tokens.
- GET /admin/activity/recent?limit=: most recently updated conversations.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter

from config import DEFAULT_MAX_TOKENS, DEFAULT_MODEL_ID, DEFAULT_TEMPERATURE
from models import (
    AnalyticsResponse,
    ConversationResponse,
    ConversationSummary,
    ModelUsageStats,
    ModelsResponse,
    SystemInfoResponse,
    TimelineDataPoint,
    TimelineResponse,
)
from storage import (
    _build_conversation_response,
    _build_conversation_summary,
    _get_all_conversations,
    _get_conversation_or_404,
    conversations,
    conversations_lock,
)

router = APIRouter()


@router.get("/admin/analytics", response_model=AnalyticsResponse)
async def get_analytics() -> AnalyticsResponse:
    """Aggregated stats: totals, averages, conversations_with_multimodal, total_files_uploaded, most_used_model."""
    all_conversations = _get_all_conversations()
    
    if not all_conversations:
        return AnalyticsResponse(
            total_conversations=0,
            total_messages=0,
            total_tokens=0,
            average_tokens_per_conversation=0.0,
            average_messages_per_conversation=0.0,
            conversations_with_multimodal=0,
            total_files_uploaded=0,
            most_used_model=None
        )
    
    total_conversations = len(all_conversations)
    total_messages = sum(conv.get('message_count', 0) for conv in all_conversations)
    total_tokens = sum(conv.get('total_tokens', 0) for conv in all_conversations)
    conversations_with_multimodal = sum(1 for conv in all_conversations if conv.get('has_multimodal', False))
    total_files_uploaded = sum(conv.get('file_count', 0) for conv in all_conversations)
    
    average_tokens_per_conversation = total_tokens / total_conversations
    average_messages_per_conversation = total_messages / total_conversations
    
    # Find most used model
    model_counts = {}
    for conv in all_conversations:
        model_id = conv.get('model_id', DEFAULT_MODEL_ID)
        model_counts[model_id] = model_counts.get(model_id, 0) + 1
    
    most_used_model = max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else None
    
    return AnalyticsResponse(
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_tokens=total_tokens,
        average_tokens_per_conversation=round(average_tokens_per_conversation, 2),
        average_messages_per_conversation=round(average_messages_per_conversation, 2),
        conversations_with_multimodal=conversations_with_multimodal,
        total_files_uploaded=total_files_uploaded,
        most_used_model=most_used_model
    )


@router.get("/admin/analytics/timeline", response_model=TimelineResponse)
async def get_analytics_timeline(days: int = 30) -> TimelineResponse:
    """Daily breakdown for the last `days`. Uses conversation created_at; fills missing dates with zeros."""
    all_conversations = _get_all_conversations()
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    daily_stats = defaultdict(lambda: {"conversations": 0, "messages": 0, "tokens": 0})

    for conv in all_conversations:
        try:
            created_date = datetime.fromisoformat(conv.get("created_at", "")).date()
            if start_date <= created_date <= end_date:
                d = created_date.isoformat()
                daily_stats[d]["conversations"] += 1
                daily_stats[d]["messages"] += conv.get("message_count", 0)
                daily_stats[d]["tokens"] += conv.get("total_tokens", 0)
        except (ValueError, AttributeError):
            continue

    timeline = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        stats = daily_stats.get(date_str, {"conversations": 0, "messages": 0, "tokens": 0})
        timeline.append(TimelineDataPoint(
            date=date_str,
            conversations=stats["conversations"],
            messages=stats["messages"],
            tokens=stats["tokens"]
        ))
        current_date += timedelta(days=1)
    
    return TimelineResponse(timeline=timeline)


@router.get("/admin/conversations", response_model=List[ConversationSummary])
async def admin_list_conversations(
    sort_by: str = "updated_at",
    order: str = "desc",
) -> List[ConversationSummary]:
    """List all conversations. sort_by: created_at|updated_at|message_count|total_tokens; order: asc|desc."""
    all_conversations = _get_all_conversations()
    reverse_order = order.lower() == "desc"
    sort_keys = {
        "created_at": lambda x: x.get("created_at", ""),
        "updated_at": lambda x: x.get("updated_at", ""),
        "message_count": lambda x: x.get("message_count", 0),
        "total_tokens": lambda x: x.get("total_tokens", 0),
    }
    sort_key = sort_keys.get(sort_by, sort_keys["updated_at"])
    all_conversations.sort(key=sort_key, reverse=reverse_order)
    
    return [_build_conversation_summary(conv) for conv in all_conversations]


@router.get("/admin/conversations/{conversation_id}", response_model=ConversationResponse)
async def admin_get_conversation(conversation_id: str) -> ConversationResponse:
    """Return full conversation by id. 404 if not found. No user check."""
    with conversations_lock:
        conversation = _get_conversation_or_404(conversation_id)
    return _build_conversation_response(conversation)


@router.get("/admin/conversations/{conversation_id}/stats", response_model=ConversationResponse)
async def admin_get_conversation_stats(conversation_id: str) -> ConversationResponse:
    """Alias for admin_get_conversation; same response shape."""
    return await admin_get_conversation(conversation_id)


@router.delete("/admin/conversations/{conversation_id}")
async def admin_delete_conversation(conversation_id: str) -> dict:
    """Delete one conversation. 404 if not found."""
    with conversations_lock:
        _get_conversation_or_404(conversation_id)
        del conversations[conversation_id]
    return {"message": f"Conversation '{conversation_id}' deleted"}


@router.post("/admin/conversations/bulk-delete")
async def admin_bulk_delete_conversations(conversation_ids: List[str]) -> dict:
    """Delete by ids. Body: JSON array of strings. Returns deleted_count, not_found[], message."""
    deleted_count = 0
    not_found = []
    
    with conversations_lock:
        for conv_id in conversation_ids:
            if conv_id in conversations:
                del conversations[conv_id]
                deleted_count += 1
            else:
                not_found.append(conv_id)
    
    return {
        "deleted_count": deleted_count,
        "not_found": not_found,
        "message": f"Deleted {deleted_count} conversation(s)"
    }


@router.get("/admin/models", response_model=ModelsResponse)
async def admin_get_models() -> ModelsResponse:
    """Per-model: conversation_count, total_tokens, average_tokens_per_conversation. Sorted by conversation_count desc."""
    all_conversations = _get_all_conversations()
    
    # Group by model
    model_stats = defaultdict(lambda: {"count": 0, "total_tokens": 0})
    
    for conv in all_conversations:
        model_id = conv.get('model_id', DEFAULT_MODEL_ID)
        model_stats[model_id]["count"] += 1
        model_stats[model_id]["total_tokens"] += conv.get('total_tokens', 0)
    
    # Build response
    models = []
    for model_id, stats in model_stats.items():
        avg_tokens = stats["total_tokens"] / stats["count"] if stats["count"] > 0 else 0.0
        models.append(ModelUsageStats(
            model_id=model_id,
            conversation_count=stats["count"],
            total_tokens=stats["total_tokens"],
            average_tokens_per_conversation=round(avg_tokens, 2)
        ))
    
    # Sort by conversation count descending
    models.sort(key=lambda x: x.conversation_count, reverse=True)
    
    return ModelsResponse(models=models)


@router.get("/admin/system", response_model=SystemInfoResponse)
async def admin_get_system_info() -> SystemInfoResponse:
    """Totals (conversations, messages, tokens) and default model_id, temperature, max_tokens."""
    all_conversations = _get_all_conversations()
    
    total_conversations = len(all_conversations)
    total_messages = sum(conv.get('message_count', 0) for conv in all_conversations)
    total_tokens = sum(conv.get('total_tokens', 0) for conv in all_conversations)
    
    return SystemInfoResponse(
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_tokens=total_tokens,
        default_model_id=DEFAULT_MODEL_ID,
        default_temperature=DEFAULT_TEMPERATURE,
        default_max_tokens=DEFAULT_MAX_TOKENS
    )


@router.get("/admin/activity/recent", response_model=List[ConversationSummary])
async def admin_get_recent_activity(limit: int = 20) -> List[ConversationSummary]:
    """Up to `limit` most recently updated conversations."""
    all_conversations = _get_all_conversations()
    
    # Sort by updated_at descending and take limit
    all_conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
    recent = all_conversations[:limit]
    
    return [_build_conversation_summary(conv) for conv in recent]
