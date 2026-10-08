import React from 'react';
import { Wrench, Play } from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import { useAuth } from '../../context/AuthContext';

export const MaintenanceBanner: React.FC = () => {
  const { settings, setMaintenanceMode, isLoading } = useSettings();
  const { isAdmin } = useAuth();

  if (!settings.maintenance_mode) return null;

  return (
    <div className="w-full bg-amber-500 text-gray-950 font-medium px-4 py-2.5 shadow-lg border-b border-amber-600 flex flex-wrap items-center justify-between gap-3 animate-pulse-slow">
      <div className="flex items-center gap-3">
        <div className="p-1.5 bg-gray-950 text-amber-400 rounded-lg">
          <Wrench className="w-5 h-5" />
        </div>
        <div>
          <span className="font-extrabold tracking-wide uppercase">SYSTEM IN MAINTENANCE MODE:</span>{' '}
          <span className="text-gray-900 text-sm">
            Live accident alerts & automated hospital dispatches are temporarily suspended. System is unavailable for emergency response.
          </span>
        </div>
      </div>

      {isAdmin && (
        <button
          onClick={() => setMaintenanceMode(false)}
          disabled={isLoading}
          className="px-4 py-1.5 bg-gray-950 hover:bg-gray-900 text-amber-300 hover:text-amber-200 text-xs font-bold uppercase tracking-wider rounded-lg transition shadow flex items-center gap-2"
        >
          <Play className="w-3.5 h-3.5 fill-amber-300" />
          Restore Live Monitoring
        </button>
      )}
    </div>
  );
};
