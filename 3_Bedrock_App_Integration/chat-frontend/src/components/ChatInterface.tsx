/**
 * Main chat UI: initial form (description + 3 images) vs follow-up input, MessageList,
 * ConversationSidebar. State: messages, conversationId, selectedFiles, conversations,
 * error, showConversations. Initial: sendInitial (multipart), then set conversationId
 * from response. Follow-up: sendFollowUp (JSON). Optimistic user message; on error,
 * roll back to `before` length. File validation: image/*, ≤3.75MB, max 3. loadConversations
 * on mount and after submit; scroll to bottom on messages change.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, FileText, Send, X } from 'lucide-react';
import { apiService } from '../services/api';
import type { ChatMessage, ConversationSummary } from '../types';
import ConversationSidebar from './ConversationSidebar';
import MessageList from './MessageList';

interface ChatInterfaceProps {
  userId: string;
}

export default function ChatInterface({ userId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConversations, setShowConversations] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadConversations = useCallback(async () => {
    try {
      const convs = await apiService.listConversations(userId);
      setConversations(convs);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }, [userId]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const onInitialFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter((f) => f.type.startsWith('image/'));
    if (files.length !== (e.target.files?.length || 0)) {
      setError('Only image files (JPEG, PNG, GIF, WebP) are supported');
      setTimeout(() => setError(null), 5000);
      e.target.value = '';
      return;
    }
    const valid = files.filter((f) => f.size <= 3.75 * 1024 * 1024);
    if (valid.length !== files.length) {
      setError('Some files exceed 3.75 MB');
      setTimeout(() => setError(null), 5000);
    }
    const next = [...selectedFiles, ...valid].slice(0, 3);
    setSelectedFiles(next);
    if (next.length >= 3 && valid.length > (3 - selectedFiles.length)) {
      setError('Maximum 3 images. Extra files ignored.');
      setTimeout(() => setError(null), 5000);
    }
    e.target.value = '';
  };

  const removeFile = (i: number) => setSelectedFiles((p) => p.filter((_, j) => j !== i));

  const submitInitial = async () => {
    const text = inputMessage.trim();
    if (!text) { setError('Please enter a description of the accident'); setTimeout(() => setError(null), 5000); return; }
    if (selectedFiles.length !== 3) {
      setError(selectedFiles.length === 0 ? 'Please upload exactly 3 photos (wide-angle, straight-on, closeup)' : `Please upload exactly 3 photos. You have ${selectedFiles.length}.`);
      setTimeout(() => setError(null), 5000);
      return;
    }
    setIsLoading(true);
    setError(null);
    const contentBlocks: Array<{ text?: string; image?: { format: string; source: { bytes: string } } }> = [{ text }];
    const imageBlocks = await Promise.all(
      selectedFiles.map(
        (f) =>
          new Promise<{ format: string; source: { bytes: string } }>((res) => {
            const r = new FileReader();
            r.onload = () => { const b = (r.result as string).split(',')[1]; res({ format: f.type.split('/')[1], source: { bytes: b } }); };
            r.readAsDataURL(f);
          })
      )
    );
    contentBlocks.push(...imageBlocks.map((b) => ({ image: b })));
    setMessages((p) => [...p, { role: 'user', content: contentBlocks }]);
    const before = messages.length;
    try {
      const res = await apiService.sendInitial(userId, text, selectedFiles);
      if (res.conversation_id) setConversationId(res.conversation_id);
      setMessages((p) => [...p, { role: 'assistant', content: res.message }]);
      setInputMessage('');
      setSelectedFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await loadConversations();
    } catch (err: any) {
      setMessages((p) => p.slice(0, before));
      const d = err.response?.data?.detail;
      setError(Array.isArray(d) ? d.map((x: { msg?: string }) => x.msg || JSON.stringify(x)).join('; ') : typeof d === 'string' ? d : d != null ? String(d) : err.message || 'Failed to send');
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const submitFollowUp = async () => {
    const text = inputMessage.trim();
    if (!text) { setError('Please enter your question'); setTimeout(() => setError(null), 5000); return; }
    if (!conversationId) { setError('No conversation'); setTimeout(() => setError(null), 5000); return; }
    setIsLoading(true);
    setError(null);
    setMessages((p) => [...p, { role: 'user', content: text }]);
    const before = messages.length;
    try {
      const res = await apiService.sendFollowUp(userId, conversationId, text);
      setMessages((p) => [...p, { role: 'assistant', content: res.message }]);
      setInputMessage('');
      await loadConversations();
    } catch (err: any) {
      setMessages((p) => p.slice(0, before));
      const d = err.response?.data?.detail;
      setError(Array.isArray(d) ? d.map((x: { msg?: string }) => x.msg || JSON.stringify(x)).join('; ') : typeof d === 'string' ? d : d != null ? String(d) : err.message || 'Failed to send');
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const onKey = (e: React.KeyboardEvent, submit: () => void) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setInputMessage('');
    setSelectedFiles([]);
    setShowConversations(false);
  };

  const handleLoadConversation = async (convId: string) => {
    try {
      const conversation = await apiService.getConversation(convId, userId);
      setMessages(conversation.messages);
      setConversationId(conversation.conversation_id);
      setShowConversations(false);
    } catch (err) {
      setError('Failed to load conversation');
      setTimeout(() => setError(null), 5000);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        currentConversationId={conversationId}
        onNewConversation={handleNewConversation}
        onLoadConversation={handleLoadConversation}
        isOpen={showConversations}
        onClose={() => setShowConversations(false)}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 shadow-sm">
          <div className="flex items-center justify-between max-w-5xl mx-auto">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowConversations(!showConversations)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Toggle conversations"
              >
                <FileText className="w-5 h-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  Automobile Damage Assessment
                </h1>
                <p className="text-sm text-gray-500">
                  {messages.length === 0 
                    ? "Submit description and exactly 3 photos (wide-angle, straight-on, closeup) for assessment"
                    : "Ask questions about your damage assessment"}
                </p>
              </div>
            </div>
            {conversationId && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                Conversation active
              </span>
            )}
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto scrollbar-thin bg-white">
          <div className="max-w-5xl mx-auto px-4 py-6">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
                  <AlertCircle className="w-8 h-8 text-primary-600" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Automobile Damage Assessment
                </h2>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Submit a description of the accident and exactly 3 photos of the vehicle damage to receive a comprehensive damage assessment.
                </p>
                <div className="bg-blue-50 p-4 rounded-lg max-w-md mx-auto text-left">
                  <h3 className="font-semibold text-gray-900 mb-2">📋 Initial Assessment Submission</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Please provide:
                  </p>
                  <ul className="text-sm text-gray-600 list-disc list-inside space-y-1 mb-3">
                    <li>A description of the accident</li>
                    <li>Exactly 3 photos of the vehicle damage (required):</li>
                  </ul>
                  <ul className="text-sm text-gray-700 list-disc list-inside space-y-1 ml-4 font-medium">
                    <li>Wide-angle photo</li>
                    <li>Straight-on photo</li>
                    <li>Closeup photo</li>
                  </ul>
                  <p className="text-sm text-gray-600 mt-3">
                    After submission, you'll receive a detailed damage assessment and can ask follow-up questions.
                  </p>
                </div>
              </div>
            ) : (
              <MessageList messages={messages} />
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mx-4 mb-2">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <p className="ml-3 text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Input: two separate UIs */}
        <div className="bg-white border-t border-gray-200 px-4 py-4">
          <div className="max-w-5xl mx-auto">
            {messages.length === 0 ? (
              /* Initial: text + exactly 3 images */
              <>
                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm font-medium text-blue-900 mb-2">📸 Upload exactly 3 photos (required):</p>
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    {[1, 2, 3].map((n) => (
                      <div key={n} className={`text-center p-2 rounded ${selectedFiles.length >= n ? 'bg-green-100 border-2 border-green-500' : 'bg-gray-100 border-2 border-dashed border-gray-300'}`}>
                        <p className="text-xs font-semibold text-gray-700">{n}. {['Wide-angle', 'Straight-on', 'Closeup'][n - 1]}</p>
                        {selectedFiles.length >= n && <span className="text-green-600 text-xs">✓</span>}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-blue-700">Click &quot;Select 3 images&quot; below. You can pick all 3 at once or add one by one. ≤ 3.75 MB each.</p>
                </div>
                {selectedFiles.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs text-gray-600 mb-2">Selected ({selectedFiles.length}/3):</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedFiles.map((f, i) => (
                        <div key={i} className="relative group bg-gray-100 rounded-lg p-2 flex items-center gap-2">
                          <img src={URL.createObjectURL(f)} alt={f.name} className="w-12 h-12 object-cover rounded" />
                          <span className="text-xs text-gray-600 max-w-[100px] truncate">{f.name}</span>
                          <button type="button" onClick={() => removeFile(i)} className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100" title="Remove"><X className="w-3 h-3" /></button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <input ref={fileInputRef} type="file" accept="image/*" multiple className="hidden" onChange={onInitialFileSelect} />
                <div className="flex items-end gap-2">
                  <div className="flex-1">
                    <textarea value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyDown={(e) => onKey(e, submitInitial)} placeholder="Describe the accident and what happened... (required)" className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 resize-y" rows={4} style={{ minHeight: '100px', maxHeight: '300px' }} disabled={isLoading} />
                  </div>
                  <div className="flex flex-col gap-2">
                    <button type="button" onClick={() => fileInputRef.current?.click()} disabled={selectedFiles.length >= 3} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm">Select 3 images</button>
                    <button type="button" onClick={submitInitial} disabled={isLoading || !inputMessage.trim() || selectedFiles.length !== 3} className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                      {isLoading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /><span>Assessing...</span></> : <><Send className="w-5 h-5" /><span>Submit Assessment</span></>}
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">Description and exactly 3 photos (wide-angle, straight-on, closeup) required. Enter to submit.</p>
              </>
            ) : (
              /* Follow-up: text only, no images */
              <div className="flex items-end gap-2">
                <textarea value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyDown={(e) => onKey(e, submitFollowUp)} placeholder="Ask a question about your damage assessment..." className="flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 resize-y" rows={3} style={{ minHeight: '80px', maxHeight: '200px' }} disabled={isLoading} />
                <button type="button" onClick={submitFollowUp} disabled={isLoading || !inputMessage.trim()} className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2 font-medium">
                  {isLoading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /><span>Sending...</span></> : <><Send className="w-5 h-5" /><span>Send</span></>}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
