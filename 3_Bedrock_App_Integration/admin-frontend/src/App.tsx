/**
 * Admin dashboard root: sidebar nav (Analytics, Conversations, Model Usage, System Info)
 * and main content. Shows a "Connecting..." spinner until GET /health succeeds; then
 * renders the selected view. Polling is handled inside Analytics, Conversations, Models, SystemInfo.
 */
import { useEffect, useState } from 'react';
import { Activity, BarChart3, Cpu, MessageSquare, Settings } from 'lucide-react';
import Analytics from './components/Analytics';
import Conversations from './components/Conversations';
import Models from './components/Models';
import SystemInfo from './components/SystemInfo';
import { apiService } from './services/api';

type View = 'analytics' | 'conversations' | 'models' | 'system';

function App() {
  const [currentView, setCurrentView] = useState<View>('analytics');
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

  const menuItems = [
    { id: 'analytics' as View, label: 'Analytics', icon: BarChart3 },
    { id: 'conversations' as View, label: 'Conversations', icon: MessageSquare },
    { id: 'models' as View, label: 'Model Usage', icon: Cpu },
    { id: 'system' as View, label: 'System Info', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-6 h-6 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Connected</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-73px)]">
          <nav className="p-4">
            <ul className="space-y-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => setCurrentView(item.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                        currentView === item.id
                          ? 'bg-primary-50 text-primary-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{item.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {currentView === 'analytics' && <Analytics />}
          {currentView === 'conversations' && <Conversations />}
          {currentView === 'models' && <Models />}
          {currentView === 'system' && <SystemInfo />}
        </main>
      </div>
    </div>
  );
}

export default App;
