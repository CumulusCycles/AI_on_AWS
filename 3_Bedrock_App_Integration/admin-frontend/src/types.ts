/**
 * Types for admin API responses and conversation/message shapes. Align with backend
 * Pydantic models and /admin/*, /conversations/* JSON. ContentBlock.image.source.bytes
 * is base64 when JSON-serialized.
 */
export interface AnalyticsResponse {
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  average_tokens_per_conversation: number;
  average_messages_per_conversation: number;
  conversations_with_multimodal: number;
  total_files_uploaded: number;
  most_used_model: string | null;
}

export interface TimelineDataPoint {
  date: string;
  conversations: number;
  messages: number;
  tokens: number;
}

export interface TimelineResponse {
  timeline: TimelineDataPoint[];
}

export interface Conversation {
  conversation_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
  model_id: string;
  temperature: number;
  max_tokens: number;
  total_tokens: number;
  message_count: number;
  has_multimodal: boolean;
  file_count: number;
}

export interface ConversationSummary {
  conversation_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  total_tokens: number;
  model_id: string;
  has_multimodal: boolean;
  file_count: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string | ContentBlock[];
}

export interface ContentBlock {
  text?: string;
  image?: {
    format: string;
    source: {
      bytes: string;
    };
  };
}

export interface ModelUsageStats {
  model_id: string;
  conversation_count: number;
  total_tokens: number;
  average_tokens_per_conversation: number;
}

export interface ModelsResponse {
  models: ModelUsageStats[];
}

export interface SystemInfoResponse {
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  default_model_id: string;
  default_temperature: number;
  default_max_tokens: number;
}
