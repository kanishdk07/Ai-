import React from 'react';
import { useSettings } from '../../context/SettingsContext';
import { Activity, Database, Calendar, Cctv, Clock, CheckCircle2, AlertTriangle } from 'lucide-react';

export const SystemHealthCard: React.FC = () => {
  const { health } = useSettings();

  const formatUptime = (seconds: number) => {
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor((seconds % (3600 * 24)) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${d}d ${h}h ${m}m`;
  };

  return (
    <div className="p-6 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between border-b border-gray-800 pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-600/20 text-emerald-400 rounded-xl">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">System Health & Telemetry</h3>
            <p className="text-xs text-gray-400 font-mono">Backend Services & Daemon Status</p>
          </div>
        </div>

        <span className="px-3 py-1 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {health.status}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
          <div className="flex items-center gap-1.5 text-gray-400 mb-1">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            <span>PostgreSQL & PostGIS</span>
          </div>
          <p className="text-sm font-bold text-emerald-400">
            {health.database_connected ? 'CONNECTED' : 'DISCONNECTED'}
          </p>
        </div>

        <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
          <div className="flex items-center gap-1.5 text-gray-400 mb-1">
            <Calendar className="w-3.5 h-3.5 text-purple-400" />
            <span>APScheduler Daemon</span>
          </div>
          <p className="text-sm font-bold text-emerald-400">
            {health.scheduler_running ? 'RUNNING' : 'STOPPED'}
          </p>
        </div>

        <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
          <div className="flex items-center gap-1.5 text-gray-400 mb-1">
            <Cctv className="w-3.5 h-3.5 text-emerald-400" />
            <span>Online Cameras</span>
          </div>
          <p className="text-sm font-bold text-white">{health.online_cameras} Active</p>
        </div>

        <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
          <div className="flex items-center gap-1.5 text-gray-400 mb-1">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Core Uptime</span>
          </div>
          <p className="text-sm font-bold text-white">{formatUptime(health.uptime_seconds || 86400)}</p>
        </div>
      </div>
    </div>
  );
};
