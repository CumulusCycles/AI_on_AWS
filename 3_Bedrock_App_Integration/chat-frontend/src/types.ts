/**
 * Types for /chat and /conversations. ChatMessage.content: string or ContentBlock[].
 * ContentBlock.image.source.bytes is base64 in JSON. ChatResponse.conversation_id
 * is set when the backend creates or uses a conversation.
 */
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

export interface ChatResponse {
  message: string;
  model_id: string;
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
    total_tokens?: number;
  };
  conversation_id?: string;
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
