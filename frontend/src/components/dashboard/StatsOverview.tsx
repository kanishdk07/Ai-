import React from 'react';
import { MetricCard } from './MetricCard';
import { useIncidents } from '../../context/IncidentContext';
import { useCameras } from '../../context/CameraContext';
import { useSettings } from '../../context/SettingsContext';
import {
  Cctv,
  AlertTriangle,
  Clock,
  CheckCheck,
  CheckCircle2,
  Bell,
  Wrench,
  Activity,
} from 'lucide-react';
import { PageId } from '../common/Sidebar';

interface StatsOverviewProps {
  onNavigate?: (page: PageId) => void;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ onNavigate }) => {
  const { incidents, unacknowledgedCount, resolvedCount, highSeverityCount } = useIncidents();
  const { cameras, monitoringCount, onlineCount, offlineCount } = useCameras();
  const { settings } = useSettings();

  const activeIncidents = incidents.filter((i) => ['detected', 'active', 'notified'].includes(i.status)).length;
  const acknowledgedIncidents = incidents.filter((i) => i.status === 'acknowledged').length;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Camera Feeds */}
      <MetricCard
        title="Active Cameras"
        value={`${monitoringCount} / ${cameras.length}`}
        subtitle={`${onlineCount} Online • ${offlineCount} Disconnected`}
        icon={Cctv}
        variant={offlineCount > 0 ? 'warning' : 'success'}
        onClick={() => onNavigate && onNavigate('cameras')}
      />

      {/* 2. Critical Incidents */}
      <MetricCard
        title="Awaiting Response"
        value={unacknowledgedCount}
        subtitle={`${highSeverityCount} High Severity Critical`}
        icon={AlertTriangle}
        variant={unacknowledgedCount > 0 ? 'danger' : 'default'}
        onClick={() => onNavigate && onNavigate('incidents')}
      />

      {/* 3. Hospital Acknowledged */}
      <MetricCard
        title="Hospital Responding"
        value={acknowledgedIncidents}
        subtitle="Ambulance Dispatched En Route"
        icon={CheckCheck}
        variant="info"
        onClick={() => onNavigate && onNavigate('notifications')}
      />

      {/* 4. Resolved Incidents */}
      <MetricCard
        title="Resolved & Cleared"
        value={resolvedCount}
        subtitle={`Total Incidents: ${incidents.length}`}
        icon={CheckCircle2}
        variant="success"
        onClick={() => onNavigate && onNavigate('incidents')}
      />

      {/* Secondary Status Row */}
      <div className="col-span-1 sm:col-span-2 lg:col-span-4 grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        {/* Automatic Notification Mode */}
        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${
              settings.auto_notification_enabled ? 'bg-emerald-950 text-emerald-400' : 'bg-amber-950 text-amber-400'
            }`}>
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">Automated Notification</p>
              <p className="text-sm font-extrabold text-white">
                {settings.auto_notification_enabled ? 'AUTO DISPATCH ACTIVE' : 'MANUAL CONFIRMATION ONLY'}
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-gray-400">
            Interval: {settings.notification_interval_seconds}s
          </span>
        </div>

        {/* Monitoring Health */}
        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-950 text-blue-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">Detection Pipeline</p>
              <p className="text-sm font-extrabold text-white">Continuous AI Inference</p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300">
            Radius: {settings.hospital_search_radius_km} km
          </span>
        </div>

        {/* Maintenance State */}
        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${
              settings.maintenance_mode ? 'bg-amber-500 text-gray-950' : 'bg-emerald-950 text-emerald-400'
            }`}>
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">System State</p>
              <p className="text-sm font-extrabold text-white">
                {settings.maintenance_mode ? 'MAINTENANCE MODE' : 'OPERATIONAL (LIVE)'}
              </p>
            </div>
          </div>
          <span className={`w-3 h-3 rounded-full ${
            settings.maintenance_mode ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'
          }`} />
        </div>
      </div>
    </div>
  );
};
