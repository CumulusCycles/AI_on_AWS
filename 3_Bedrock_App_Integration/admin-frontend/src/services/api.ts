/**
 * Admin API client. Axios instance with baseURL from config. All /admin/* and /health
 * calls. listConversations uses sort_by and order query params; getAnalyticsTimeline uses days.
 */
import axios from 'axios';
import { API_BASE_URL } from '../config';
import type {
  AnalyticsResponse,
  Conversation,
  ConversationSummary,
  ModelsResponse,
  SystemInfoResponse,
  TimelineResponse,
} from '../types';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const apiService = {
  async healthCheck(): Promise<{ status: string }> {
    const { data } = await api.get('/health');
    return data;
  },

  async getAnalytics(): Promise<AnalyticsResponse> {
    const { data } = await api.get('/admin/analytics');
    return data;
  },

  async getAnalyticsTimeline(days: number = 30): Promise<TimelineResponse> {
    const { data } = await api.get(`/admin/analytics/timeline?days=${days}`);
    return data;
  },

  async listConversations(
    sortBy: string = 'updated_at',
    order: 'asc' | 'desc' = 'desc'
  ): Promise<ConversationSummary[]> {
    const { data } = await api.get(`/admin/conversations?sort_by=${sortBy}&order=${order}`);
    return data;
  },

  async getConversation(conversationId: string): Promise<Conversation> {
    const { data } = await api.get(`/admin/conversations/${conversationId}`);
    return data;
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await api.delete(`/admin/conversations/${conversationId}`);
  },

  async getModelUsage(): Promise<ModelsResponse> {
    const { data } = await api.get('/admin/models');
    return data;
  },

  async getSystemInfo(): Promise<SystemInfoResponse> {
    const { data } = await api.get('/admin/system');
    return data;
  },
};
