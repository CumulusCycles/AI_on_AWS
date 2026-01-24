/**
 * Conversations tab: table of all conversations (search, sort, order), view detail, delete.
 * listConversations(sortBy, order) and getConversation(id), deleteConversation(id). Polls list
 * on sort/order change and poll interval; when a conversation is selected, also polls that
 * conversation. Multimodal conversations show an image icon; detail view renders messages
 * (text and inline images via data URL from base64).
 */
import { useEffect, useState } from 'react';
import { Eye, Image as ImageIcon, Search, Trash2 } from 'lucide-react';
import { POLLING_INTERVAL } from '../config';
import { apiService } from '../services/api';
import type { Conversation, ConversationSummary } from '../types';

export default function Conversations() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('updated_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  const loadConversations = async () => {
    setLoading(true);
    try {
      const data = await apiService.listConversations(sortBy, order);
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, [sortBy, order]);

  const handleViewConversation = async (conversationId: string) => {
    try {
      const conversation = await apiService.getConversation(conversationId);
      setSelectedConversation(conversation);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  // Poll for conversation updates when viewing a specific conversation
  useEffect(() => {
    if (!selectedConversation) return;
    
    const interval = setInterval(async () => {
      try {
        const conversation = await apiService.getConversation(selectedConversation.conversation_id);
        setSelectedConversation(conversation);
      } catch (error) {
        console.error('Failed to refresh conversation:', error);
      }
    }, POLLING_INTERVAL);
    
    return () => clearInterval(interval);
  }, [selectedConversation?.conversation_id]);

  const handleDeleteConversation = async (conversationId: string) => {
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }
    try {
      await apiService.deleteConversation(conversationId);
      await loadConversations();
      if (selectedConversation?.conversation_id === conversationId) {
        setSelectedConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('Failed to delete conversation');
    }
  };

  const filteredConversations = conversations.filter((conv) =>
    conv.conversation_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    conv.user_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (selectedConversation) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSelectedConversation(null)}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            ← Back to Conversations
          </button>
          <button
            onClick={() => handleDeleteConversation(selectedConversation.conversation_id)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Conversation Details</h2>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600">Conversation ID</p>
              <p className="font-mono text-sm">{selectedConversation.conversation_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">User ID</p>
              <p className="font-mono text-sm">{selectedConversation.user_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Model</p>
              <p className="text-sm">{selectedConversation.model_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Messages</p>
              <p className="text-sm">{selectedConversation.message_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Tokens</p>
              <p className="text-sm">{selectedConversation.total_tokens.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Created</p>
              <p className="text-sm">{formatDate(selectedConversation.created_at)}</p>
            </div>
          </div>

          <div className="border-t pt-4">
            <h3 className="font-semibold text-gray-900 mb-3">Messages</h3>
            <div className="space-y-4 max-h-96 overflow-y-auto scrollbar-thin">
              {selectedConversation.messages.map((msg, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg ${
                    msg.role === 'user' ? 'bg-blue-50' : 'bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-semibold text-gray-600 uppercase">
                      {msg.role}
                    </span>
                  </div>
                  {typeof msg.content === 'string' ? (
                    <p className="text-sm text-gray-900 whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div className="space-y-2">
                      {msg.content.map((block, blockIndex) => (
                        <div key={blockIndex}>
                          {block.text && (
                            <p className="text-sm text-gray-900 whitespace-pre-wrap">{block.text}</p>
                          )}
                          {block.image && (
                            <img
                              src={`data:image/${block.image.format};base64,${block.image.source.bytes}`}
                              alt="Uploaded"
                              className="max-w-xs rounded-lg border border-gray-200 mt-2"
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Conversations</h2>
        <div className="flex items-center gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="updated_at">Sort by Updated</option>
            <option value="created_at">Sort by Created</option>
            <option value="message_count">Sort by Messages</option>
            <option value="total_tokens">Sort by Tokens</option>
          </select>
          <button
            onClick={() => setOrder(order === 'asc' ? 'desc' : 'asc')}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {order === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search by conversation ID or user ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Conversations List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Conversation ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Messages
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tokens
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Updated
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredConversations.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No conversations found
                  </td>
                </tr>
              ) : (
                filteredConversations.map((conv) => (
                  <tr key={conv.conversation_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-gray-900">
                          {conv.conversation_id.substring(0, 8)}...
                        </span>
                        {conv.has_multimodal && (
                          <span title="Has images">
                            <ImageIcon className="w-4 h-4 text-blue-500" />
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-mono text-sm text-gray-600">{conv.user_id}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {conv.message_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {conv.total_tokens.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(conv.updated_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleViewConversation(conv.conversation_id)}
                          className="text-primary-600 hover:text-primary-700"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteConversation(conv.conversation_id)}
                          className="text-red-600 hover:text-red-700"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-sm text-gray-500 text-center">
        Showing {filteredConversations.length} of {conversations.length} conversations
      </div>
    </div>
  );
}
