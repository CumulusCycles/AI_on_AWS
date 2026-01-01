import { useState, useEffect, useRef } from 'react';
import ChatPane from './components/ChatPane';
import { ChatMessage, PersonConfig } from './types';

const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

const PERSONS: PersonConfig[] = [
  { id: 'person1', name: 'Person 1', language: 'English', languageCode: 'en' },
  { id: 'person2', name: 'Person 2', language: 'Spanish', languageCode: 'es' },
  { id: 'person3', name: 'Person 3', language: 'French', languageCode: 'fr' },
];

function App() {
  const [messages, setMessages] = useState<Record<string, ChatMessage[]>>({
    person1: [],
    person2: [],
    person3: [],
  });
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isConnectingRef = useRef<boolean>(false);

  const connectWebSocket = () => {
    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current) {
      console.log('Connection attempt already in progress, skipping...');
      return;
    }

    // Don't connect if already connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      setIsConnected(true);
      return;
    }

    try {
      isConnectingRef.current = true;
      console.log('Attempting to connect to WebSocket at:', WS_URL);
      const ws = new WebSocket(WS_URL);

      ws.onopen = (event) => {
        console.log('✅ WebSocket connected successfully!', event);
        console.log('WebSocket readyState:', ws.readyState);
        console.log('WebSocket protocol:', ws.protocol);
        isConnectingRef.current = false;
        setIsConnected(true);
        // Clear any pending reconnection
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'message' && data.messages) {
            // Update messages for each person
            setMessages((prev) => {
              const newMessages = { ...prev };
              Object.keys(data.messages).forEach((personId) => {
                const message = {
                  ...data.messages[personId],
                  timestamp: data.timestamp || Date.now(),
                };
                newMessages[personId] = [...(newMessages[personId] || []), message];
              });
              return newMessages;
            });
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket readyState:', ws.readyState);
        console.error('WebSocket URL attempted:', WS_URL);
        console.error('WebSocket URL type:', typeof WS_URL);
        isConnectingRef.current = false;
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        console.log('Close code:', event.code, 'Close reason:', event.reason || 'No reason provided');
        isConnectingRef.current = false;
        setIsConnected(false);
        
        // Only reconnect if it wasn't a manual close
        if (event.code !== 1000) {
          console.log('Attempting to reconnect in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
              connectWebSocket();
            }
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      console.error('WebSocket URL:', WS_URL);
      isConnectingRef.current = false;
      setIsConnected(false);
      // Retry connection after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    }
  };

  useEffect(() => {
    // Only connect if we don't already have an active connection
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      connectWebSocket();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, []);

  const handleSendMessage = (text: string, sender: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          sender,
          text,
          timestamp: Date.now(),
        })
      );
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-full px-4 py-3">
          <h1 className="text-2xl font-bold text-gray-900">Multilingual Chat</h1>
          <p className="text-sm text-gray-600">
            Three people chatting in different languages with real-time translation
          </p>
        </div>
      </header>

      {/* Chat Panes */}
      <div className="h-[calc(100vh-100px)] flex gap-4 px-4">
        {PERSONS.map((person) => (
          <ChatPane
            key={person.id}
            person={person}
            messages={messages[person.id] || []}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="bg-white border-t border-gray-300 px-4 py-2">
        <div className="flex items-center justify-end gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 bg-blue-600 rounded"></span>
            <span>Your messages</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 bg-green-600 rounded"></span>
            <span>Positive sentiment</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 bg-black rounded"></span>
            <span>Neutral sentiment</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 bg-red-600 rounded"></span>
            <span>Negative sentiment</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

