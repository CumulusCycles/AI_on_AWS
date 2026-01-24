/**
 * Damage Assessment root: persistent userId (localStorage) and backend health check.
 * Shows "Connecting..." until GET /health succeeds, then ChatInterface. userId is
 * used for /chat and /conversations?user_id= and /conversations/:id?user_id=.
 */
import { useEffect, useState } from 'react';
import ChatInterface from './components/ChatInterface';
import { apiService } from './services/api';

function App() {
  const [userId] = useState(() => {
    const stored = localStorage.getItem('accident_assessment_user_id');
    if (stored) return stored;
    const newId = `user-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
    localStorage.setItem('accident_assessment_user_id', newId);
    return newId;
  });

  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    apiService
      .healthCheck()
      .then(() => setIsConnected(true))
      .catch(() => setIsConnected(false));
  }, []);

  if (!isConnected) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to server...</p>
          <p className="text-sm text-gray-500 mt-2">
            Make sure the backend server is running on http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
      <ChatInterface userId={userId} />
    </div>
  );
}

export default App;
