import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getDashboards, getDashboardMetrics, Dashboard as DashboardType, Metric } from '../services/api';
import webSocketManager from '../services/websocket';
import {
  ArrowLeftOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  ChartBarIcon,
  TrashIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';

import MetricCard from '../components/MetricCard';
import MetricChart, { MetricDataPoint } from '../components/MetricChart';

type MetricState = Metric & { previousValue?: number };

const Dashboard: React.FC = () => {
  const { user, logout, token } = useAuth();

  const [dashboards, setDashboards] = useState<DashboardType[]>([]);
  const [loadingDashboards, setLoadingDashboards] = useState(true);
  const [dashboardsError, setDashboardsError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [selectedDashboardId, setSelectedDashboardId] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<MetricState[]>([]);
  const [metricsHistory, setMetricsHistory] = useState<Record<string, MetricDataPoint[]>>({});
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [metricsError, setMetricsError] = useState<string | null>(null);

  const fetchDashboards = async () => {
    try {
      setLoadingDashboards(true);
      const userDashboards = await getDashboards();
      setDashboards(userDashboards);
    } catch (err: any) {
      setDashboardsError(err.message || 'Failed to fetch dashboards');
    } finally {
      setLoadingDashboards(false);
    }
  };

  useEffect(() => {
    fetchDashboards();
  }, []);

  const handleDashboardSelect = async (dashboardId: number) => {
    if (selectedDashboardId === dashboardId) return;

    setSelectedDashboardId(dashboardId);
    setSidebarOpen(false);
    setMetrics([]);
    setMetricsHistory({});
    setMetricsError(null);
    setLoadingMetrics(true);

    try {
      const initialMetrics = await getDashboardMetrics(dashboardId);
      const initialHistory: Record<string, MetricDataPoint[]> = {};
      initialMetrics.forEach(metric => {
        initialHistory[metric.name] = [{
          timestamp: metric.created_at,
          value: metric.value
        }];
      });
      setMetrics(initialMetrics);
      setMetricsHistory(initialHistory);
    } catch (err: any) {
      setMetricsError(err.message || 'Failed to fetch metrics');
    } finally {
      setLoadingMetrics(false);
    }
  };

  useEffect(() => {
    if (selectedDashboardId && token) {
      webSocketManager.connect(selectedDashboardId, token);

      webSocketManager.onMessage((message) => {
        if (message.type === 'metric_update') {
          const updatedMetric: Metric = message.data;

          console.log('WebSocket metric update:', updatedMetric);

          setMetrics(prevMetrics => {
            // Find existing metric by name first (more reliable than ID for updates)
            const existingIndex = prevMetrics.findIndex(m => m.name === updatedMetric.name);

            if (existingIndex !== -1) {
              // Update existing metric
              const updated = [...prevMetrics];
              updated[existingIndex] = {
                ...updatedMetric,
                previousValue: prevMetrics[existingIndex].value,
              };
              console.log('Updated metric at index', existingIndex, updated[existingIndex]);
              return updated;
            } else {
              // Add new metric
              console.log('Adding new metric:', updatedMetric);
              return [...prevMetrics, updatedMetric];
            }
          });

          setMetricsHistory(prevHistory => {
            const newHistory = {
              ...prevHistory,
              [updatedMetric.name]: [
                ...(prevHistory[updatedMetric.name] || []),
                { timestamp: updatedMetric.created_at, value: updatedMetric.value },
              ].slice(-100),
            };
            console.log('Updated history for', updatedMetric.name, newHistory[updatedMetric.name].length, 'points');
            return newHistory;
          });
        }
      });

      return () => {
        console.log('Disconnecting WebSocket');
        webSocketManager.disconnect();
      };
    }
  }, [selectedDashboardId, token]);

  const handleCreateDashboard = async () => {
    const name = prompt('Enter new dashboard name:');
    if (name && token) {
      try {
        await fetch('http://localhost:8000/api/v1/dashboards/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ name, description: '' }),
        });
        fetchDashboards(); // Refresh dashboard list
      } catch (err) {
        alert('Failed to create dashboard');
      }
    }
  };

  const handleDeleteDashboard = async (dashboardId: number) => {
    if (confirm('Are you sure you want to delete this dashboard and all its metrics?')) {
      try {
        await fetch(`http://localhost:8000/api/v1/dashboards/${dashboardId}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        setDashboards(prev => prev.filter(d => d.id !== dashboardId));
        if (selectedDashboardId === dashboardId) {
          setSelectedDashboardId(null);
          setMetrics([]);
          setMetricsHistory({});
        }
      } catch (err) {
        alert('Failed to delete dashboard');
      }
    }
  };

  const handleCreateMetric = async () => {
    if (!selectedDashboardId) return;
    const name = prompt('Metric name (e.g., cpu_usage):');
    if (name && token) {
      const value = parseFloat(prompt('Initial value:') || '0');
      const type = prompt('Type (gauge/counter):') || 'gauge';
      try {
        await fetch('http://localhost:8000/api/v1/metrics/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify([{ dashboard_id: selectedDashboardId, name, value, metric_type: type }]),
        });
        // Metric will update via WebSocket
      } catch (err) {
        alert('Failed to create metric');
      }
    }
  };

  const handleDeleteMetric = async (metricId: number) => {
    if (confirm('Are you sure you want to delete this metric?')) {
      try {
        await fetch(`http://localhost:8000/api/v1/metrics/${metricId}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        setMetrics(prev => prev.filter(m => m.id !== metricId));
      } catch (err) {
        alert('Failed to delete metric');
      }
    }
  };

  const selectedDashboard = dashboards.find(d => d.id === selectedDashboardId);

  const renderContent = () => {
    if (!selectedDashboardId) {
      return (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <ChartBarIcon className="mx-auto h-12 w-12 text-gray-500" />
            <h2 className="mt-2 text-2xl font-semibold text-gray-400">Select a dashboard</h2>
            <p className="mt-1 text-gray-500">Choose or create a dashboard to view its real-time metrics.</p>
          </div>
        </div>
      );
    }

    if (loadingMetrics) return <div className="text-center p-10">Loading metrics...</div>;
    if (metricsError) return <div className="text-center p-10 text-red-400">{metricsError}</div>;

    return (
      <div className="w-full">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold">{selectedDashboard?.name}</h2>
          <button
            onClick={handleCreateMetric}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Metric
          </button>
        </div>

        {metrics.length === 0 ? (
          <div className="text-center py-20 border-2 border-dashed border-gray-700 rounded-lg">
            <p className="text-gray-400">No metrics found for this dashboard.</p>
            <p className="text-gray-500 text-sm">Click "+ Add Metric" to get started.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {metrics.map((metric) => (
                <div key={metric.id} className="relative group">
                  <MetricCard
                    name={metric.name}
                    value={metric.value}
                    type={metric.metric_type}
                    previousValue={metric.previousValue}
                  />
                  <button
                    onClick={() => handleDeleteMetric(metric.id)}
                    className="absolute top-2 right-2 p-1 bg-gray-700 rounded-full text-gray-400 opacity-0 group-hover:opacity-100 hover:bg-red-600 hover:text-white transition-opacity"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            <div className="mt-8 space-y-8">
              {metrics.map((metric) => (
                <MetricChart
                  key={metric.id}
                  metricName={metric.name}
                  metricType={metric.metric_type}
                  data={metricsHistory[metric.name] || []}
                />
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <aside
        className={`bg-gray-800 text-white w-64 space-y-6 py-7 px-2 absolute inset-y-0 left-0 transform ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:relative md:translate-x-0 transition duration-200 ease-in-out z-20 flex flex-col`}
      >
        <h2 className="text-2xl font-semibold text-center px-2">Dashboards</h2>
        <nav className="flex-grow px-2">
          {loadingDashboards && <p className="text-center">Loading...</p>}
          {dashboardsError && <p className="text-center text-red-400">{dashboardsError}</p>}
          <div className="space-y-1">
            {dashboards.map((dashboard) => (
              <div key={dashboard.id} className="relative group">
                <button
                  onClick={() => handleDashboardSelect(dashboard.id)}
                  className={`block w-full text-left py-2.5 px-4 rounded transition duration-200 ${
                    selectedDashboardId === dashboard.id
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-700'
                  }`}
                >
                  {dashboard.name}
                </button>
                <button
                  onClick={() => handleDeleteDashboard(dashboard.id)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-opacity"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </nav>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700 flex-shrink-0">
          <div className="flex items-center">
            <button className="text-white md:hidden mr-4" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? <XMarkIcon className="h-6 w-6" /> : <Bars3Icon className="h-6 w-6" />}
            </button>
            <h1 className="text-xl font-bold">InsightBoard</h1>
            <button
              onClick={handleCreateDashboard}
              className="ml-6 flex items-center px-3 py-1.5 border border-gray-600 text-sm text-gray-300 rounded-md hover:bg-gray-700 hover:text-white transition-colors"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Create Dashboard
            </button>
          </div>
          <div className="flex items-center">
            <span className="mr-4 hidden sm:inline">{user?.email}</span>
            <button onClick={logout} className="flex items-center px-3 py-2 bg-red-600 rounded-md hover:bg-red-700 transition-colors">
              <ArrowLeftOnRectangleIcon className="h-5 w-5 sm:mr-2" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>

        <main className="flex-1 p-6 lg:p-10 overflow-y-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
