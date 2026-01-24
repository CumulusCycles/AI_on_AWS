/**
 * System Info tab: system overview (totals), default config (model, temperature, max_tokens),
 * status indicator. Polls /admin/system every POLLING_INTERVAL.
 */
import { useEffect, useState } from 'react';
import { Activity, Server, Settings } from 'lucide-react';
import { POLLING_INTERVAL } from '../config';
import { apiService } from '../services/api';
import type { SystemInfoResponse } from '../types';

export default function SystemInfo() {
  const [systemInfo, setSystemInfo] = useState<SystemInfoResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSystemInfo();
    
    // Poll for updates at configured interval
    const interval = setInterval(() => {
      loadSystemInfo();
    }, POLLING_INTERVAL);
    
    return () => clearInterval(interval);
  }, []);

  const loadSystemInfo = async () => {
    setLoading(true);
    try {
      const data = await apiService.getSystemInfo();
      setSystemInfo(data);
    } catch (error) {
      console.error('Failed to load system info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!systemInfo) {
    return <div className="text-center text-gray-500">No system information available</div>;
  }

  const infoSections = [
    {
      title: 'System Overview',
      icon: Server,
      items: [
        { label: 'Total Conversations', value: systemInfo.total_conversations.toLocaleString() },
        { label: 'Total Messages', value: systemInfo.total_messages.toLocaleString() },
        { label: 'Total Tokens', value: systemInfo.total_tokens.toLocaleString() },
      ],
    },
    {
      title: 'Default Configuration',
      icon: Settings,
      items: [
        { label: 'Default Model', value: systemInfo.default_model_id },
        { label: 'Default Temperature', value: systemInfo.default_temperature.toString() },
        { label: 'Default Max Tokens', value: systemInfo.default_max_tokens.toLocaleString() },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">System Information</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {infoSections.map((section, index) => {
          const Icon = section.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-primary-100 p-2 rounded-lg">
                  <Icon className="w-5 h-5 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
              </div>
              <div className="space-y-3">
                {section.items.map((item, itemIndex) => (
                  <div key={itemIndex} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                    <span className="text-sm text-gray-600">{item.label}</span>
                    <span className="text-sm font-medium text-gray-900">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-green-100 p-2 rounded-lg">
            <Activity className="w-5 h-5 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600">System is operational</span>
        </div>
      </div>
    </div>
  );
}
