/**
 * Chat frontend API: /health, /chat (sendInitial via fetch+FormData, sendFollowUp via axios),
 * /conversations (list, get). sendInitial uses fetch so the browser sets multipart
 * boundaries; axios is used for JSON and /conversations. API_BASE_URL from VITE_API_URL.
 */
import axios from 'axios';
import type { ChatResponse, Conversation, ConversationSummary } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const apiService = {
  async healthCheck(): Promise<{ status: string }> {
    const { data } = await api.get('/health');
    return data;
  },

  /** POST /chat multipart: user_id, message, files (exactly 3 for initial). Returns ChatResponse. */
  async sendInitial(userId: string, message: string, files: File[]): Promise<ChatResponse> {
    const form = new FormData();
    form.append('user_id', userId);
    form.append('message', message);
    files.forEach((f) => form.append('files', f));
    const res = await fetch(`${API_BASE_URL}/chat`, { method: 'POST', body: form });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const e = new Error(typeof body?.detail === 'string' ? body.detail : body?.detail?.msg || res.statusText) as Error & { response?: { data?: { detail?: unknown }; status?: number } };
      e.response = { data: { detail: body?.detail }, status: res.status };
      throw e;
    }
    return body as ChatResponse;
  },

  /** POST /chat JSON: user_id, conversation_id, message. No files. */
  async sendFollowUp(userId: string, conversationId: string, message: string): Promise<ChatResponse> {
    const { data } = await api.post<ChatResponse>('/chat', {
      user_id: userId,
      conversation_id: conversationId,
      message,
    });
    return data;
  },

  async listConversations(userId: string): Promise<ConversationSummary[]> {
    const { data } = await api.get<ConversationSummary[]>(`/conversations?user_id=${userId}`);
    return data;
  },

  async getConversation(conversationId: string, userId: string): Promise<Conversation> {
    const { data } = await api.get<Conversation>(`/conversations/${conversationId}?user_id=${userId}`);
    return data;
  },
};
