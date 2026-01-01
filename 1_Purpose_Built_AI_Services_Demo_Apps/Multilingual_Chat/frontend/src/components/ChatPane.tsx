import { useState, useEffect, useRef } from 'react';
import { ChatMessage, PersonConfig } from '../types';

interface ChatPaneProps {
  person: PersonConfig;
  messages: ChatMessage[];
  onSendMessage: (text: string, sender: string) => void;
  isConnected: boolean;
}

export default function ChatPane({ person, messages, onSendMessage, isConnected }: ChatPaneProps) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim() && isConnected) {
      onSendMessage(inputText.trim(), person.id);
      setInputText('');
    }
  };

  const getColorClass = (color: string) => {
    switch (color) {
      case 'blue':
        return 'text-blue-600 font-semibold';
      case 'green':
        return 'text-green-600 font-semibold';
      case 'red':
        return 'text-red-600 font-semibold';
      default:
        return 'text-black';
    }
  };

  return (
    <div className="flex flex-col h-full border border-gray-300 rounded-lg shadow-sm bg-white flex-1">
      {/* Header */}
      <div className="bg-gray-100 p-4 border-b border-gray-300">
        <h2 className="text-lg font-bold">{person.name}</h2>
        <p className="text-sm text-gray-600">{person.language}</p>
        <div className="mt-2 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-xs text-gray-500">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-8">
            <p>No messages yet. Start chatting!</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg ${
                msg.sender === person.id ? 'bg-blue-50 ml-auto max-w-[80%]' : 'bg-white mr-auto max-w-[80%]'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold text-gray-600">
                  {msg.sender === 'person1' ? 'Person 1' : msg.sender === 'person2' ? 'Person 2' : 'Person 3'}
                </span>
                {msg.sentiment && (
                  <span className="text-xs text-gray-400">
                    ({msg.sentiment})
                  </span>
                )}
              </div>
              <p className={getColorClass(msg.color)}>{msg.text}</p>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-300 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={`Type a message in ${person.language}...`}
            disabled={!isConnected}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || !isConnected}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

