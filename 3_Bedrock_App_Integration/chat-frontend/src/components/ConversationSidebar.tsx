/**
 * Sidebar: list of conversations (message count, relative date, multimodal badge), New,
 * and close. On mobile, overlay when open; sliding panel. formatDate: Today, Yesterday,
 * N days ago, or toLocaleDateString. Highlights currentConversationId. Parent controls
 * isOpen and onClose for the toggle.
 */
import { Calendar, MessageSquare, Plus, X } from 'lucide-react';
import type { ConversationSummary } from '../types';

interface ConversationSidebarProps {
  conversations: ConversationSummary[];
  currentConversationId: string | null;
  onNewConversation: () => void;
  onLoadConversation: (conversationId: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function ConversationSidebar({
  conversations,
  currentConversationId,
  onNewConversation,
  onLoadConversation,
  isOpen,
  onClose,
}: ConversationSidebarProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 w-80 bg-white border-r border-gray-200 z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        } flex flex-col`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={onNewConversation}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="New conversation"
            >
              <Plus className="w-5 h-5 text-gray-600" />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors md:hidden"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No conversations yet</p>
              <p className="text-xs mt-1">Start a new conversation to begin</p>
            </div>
          ) : (
            <div className="p-2">
              {conversations.map((conv) => (
                <button
                  key={conv.conversation_id}
                  onClick={() => onLoadConversation(conv.conversation_id)}
                  className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                    currentConversationId === conv.conversation_id
                      ? 'bg-primary-50 border border-primary-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-gray-400" />
                      <span className="text-xs font-medium text-gray-500">
                        {conv.message_count} messages
                      </span>
                    </div>
                    {conv.has_multimodal && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                        📸
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Calendar className="w-3 h-3" />
                    <span>{formatDate(conv.updated_at)}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
