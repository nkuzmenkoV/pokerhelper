import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface StatusData {
  status: string;
  app: {
    name: string;
    version: string;
    debug: boolean;
  };
  charts: {
    loaded: string[];
    total_ranges: number;
  };
  connections: {
    websocket: number;
  };
  model: {
    loaded: boolean;
    path: string;
  };
}

function StatusBadge({ status }: { status: string }) {
  const isHealthy = status === 'healthy';
  return (
    <span className={`
      inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium
      ${isHealthy 
        ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
        : 'bg-red-500/20 text-red-400 border border-red-500/30'
      }
    `}>
      <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-green-400' : 'bg-red-400'}`}></span>
      {status}
    </span>
  );
}

function StatCard({ 
  title, 
  value, 
  icon, 
  status = 'default' 
}: { 
  title: string; 
  value: string | number; 
  icon: string;
  status?: 'good' | 'warning' | 'bad' | 'default';
}) {
  const statusColors = {
    good: 'text-green-400',
    warning: 'text-yellow-400',
    bad: 'text-red-400',
    default: 'text-white',
  };

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">{title}</p>
          <p className={`text-2xl font-bold mt-1 ${statusColors[status]}`}>{value}</p>
        </div>
        <span className="text-2xl opacity-50">{icon}</span>
      </div>
    </div>
  );
}

export function StatusPage() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchStatus = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  useEffect(() => {
    fetchStatus();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link to="/" className="text-gray-500 hover:text-white text-sm mb-2 inline-block">
              ← Back to Dashboard
            </Link>
            <h1 className="text-2xl font-bold text-white">System Status</h1>
            <p className="text-gray-500 text-sm mt-1">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </p>
          </div>
          <button 
            onClick={fetchStatus}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-500">Loading status...</p>
          </div>
        ) : error ? (
          <div className="glass-elevated rounded-xl p-6 text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-red-400 mb-2">Connection Error</h2>
            <p className="text-gray-500">{error}</p>
            <button 
              onClick={fetchStatus}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        ) : status ? (
          <div className="space-y-6">
            {/* Overall Status */}
            <div className="glass-elevated rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">{status.app.name}</h2>
                  <p className="text-sm text-gray-500">Version {status.app.version}</p>
                </div>
                <StatusBadge status={status.status} />
              </div>
              
              {status.app.debug && (
                <div className="mt-4 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                  <p className="text-yellow-400 text-sm">⚠️ Debug mode is enabled</p>
                </div>
              )}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard 
                title="Charts Loaded" 
                value={status.charts.loaded.length}
                icon="📊"
                status={status.charts.loaded.length > 0 ? 'good' : 'warning'}
              />
              <StatCard 
                title="Total Ranges" 
                value={status.charts.total_ranges}
                icon="🎯"
                status={status.charts.total_ranges > 0 ? 'good' : 'warning'}
              />
              <StatCard 
                title="WebSocket" 
                value={status.connections.websocket}
                icon="🔌"
                status="default"
              />
              <StatCard 
                title="ML Model" 
                value={status.model.loaded ? 'Loaded' : 'Not Loaded'}
                icon="🤖"
                status={status.model.loaded ? 'good' : 'warning'}
              />
            </div>

            {/* Charts Section */}
            <div className="glass rounded-xl p-6">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
                Loaded Charts
              </h3>
              {status.charts.loaded.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {status.charts.loaded.map((chart) => (
                    <div 
                      key={chart}
                      className="px-3 py-2 bg-green-500/10 border border-green-500/30 rounded-lg text-center"
                    >
                      <span className="text-green-400 text-sm font-mono">{chart}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No charts loaded</p>
              )}
            </div>

            {/* Model Section */}
            <div className="glass rounded-xl p-6">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
                ML Model
              </h3>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-mono text-sm">{status.model.path}</p>
                  <p className="text-gray-500 text-xs mt-1">
                    {status.model.loaded 
                      ? '✓ Model is loaded and ready' 
                      : '○ Model not loaded - using fallback detection'
                    }
                  </p>
                </div>
                <span className={`
                  w-3 h-3 rounded-full
                  ${status.model.loaded ? 'bg-green-400' : 'bg-gray-600'}
                `}></span>
              </div>
            </div>

            {/* Links */}
            <div className="flex gap-4">
              <a 
                href="/metrics"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 glass rounded-xl p-4 hover:bg-white/5 transition-colors"
              >
                <h4 className="font-semibold text-white">Prometheus Metrics</h4>
                <p className="text-sm text-gray-500 mt-1">View raw metrics data</p>
              </a>
              <a 
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 glass rounded-xl p-4 hover:bg-white/5 transition-colors"
              >
                <h4 className="font-semibold text-white">API Documentation</h4>
                <p className="text-sm text-gray-500 mt-1">OpenAPI/Swagger docs</p>
              </a>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
