/**
 * Analytics tab: stat cards, timeline charts (conversations/messages/tokens), most-used model.
 * Fetches /admin/analytics and /admin/analytics/timeline?days= on mount and every POLLING_INTERVAL.
 * days can be 7, 30, or 90. Recharts LineChart/BarChart for timelines.
 */
import { useEffect, useState } from 'react';
import { Cpu, FileText, Image, MessageSquare, TrendingUp, Upload, Zap } from 'lucide-react';
import { BarChart, Bar, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { POLLING_INTERVAL } from '../config';
import { apiService } from '../services/api';
import type { AnalyticsResponse, TimelineDataPoint } from '../types';

export default function Analytics() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [timeline, setTimeline] = useState<TimelineDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [analyticsData, timelineData] = await Promise.all([
          apiService.getAnalytics(),
          apiService.getAnalyticsTimeline(days),
        ]);
        setAnalytics(analyticsData);
        setTimeline(timelineData.timeline);
      } catch (error) {
        console.error('Failed to load analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Poll for updates at configured interval
    const interval = setInterval(fetchData, POLLING_INTERVAL);
    
    return () => clearInterval(interval);
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!analytics) {
    return <div className="text-center text-gray-500">No analytics data available</div>;
  }

  const statCards = [
    {
      title: 'Total Conversations',
      value: analytics.total_conversations.toLocaleString(),
      icon: MessageSquare,
      color: 'bg-blue-500',
    },
    {
      title: 'Total Messages',
      value: analytics.total_messages.toLocaleString(),
      icon: FileText,
      color: 'bg-green-500',
    },
    {
      title: 'Total Tokens',
      value: analytics.total_tokens.toLocaleString(),
      icon: Zap,
      color: 'bg-yellow-500',
    },
    {
      title: 'Multimodal Conversations',
      value: analytics.conversations_with_multimodal.toLocaleString(),
      icon: Image,
      color: 'bg-purple-500',
    },
    {
      title: 'Files Uploaded',
      value: analytics.total_files_uploaded.toLocaleString(),
      icon: Upload,
      color: 'bg-pink-500',
    },
    {
      title: 'Avg Messages/Conv',
      value: analytics.average_messages_per_conversation.toFixed(1),
      icon: TrendingUp,
      color: 'bg-indigo-500',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversations Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="conversations" stroke="#3b82f6" name="Conversations" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Messages Timeline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Messages Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="messages" stroke="#10b981" name="Messages" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Tokens Timeline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tokens Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="tokens" fill="#f59e0b" name="Tokens" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Most Used Model */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Most Used Model</h3>
          {analytics.most_used_model ? (
            <div className="flex items-center justify-center h-[300px]">
              <div className="text-center">
                <Cpu className="w-16 h-16 text-primary-600 mx-auto mb-4" />
                <p className="text-2xl font-bold text-gray-900">{analytics.most_used_model}</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No model usage data
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
