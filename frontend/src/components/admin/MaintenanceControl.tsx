import React, { useState } from 'react';
import { useSettings } from '../../context/SettingsContext';
import { Wrench, Power, AlertTriangle, Play } from 'lucide-react';

export const MaintenanceControl: React.FC = () => {
  const { settings, setMaintenanceMode, isLoading } = useSettings();
  const [reason, setReason] = useState<string>('Scheduled CCTV Server & Database System Maintenance');

  const toggleMaintenance = async () => {
    const nextState = !settings.maintenance_mode;
    if (nextState) {
      if (
        window.confirm(
          'ARE YOU SURE? Enabling Maintenance Mode will pause live emergency monitoring and prevent new notifications from being dispatched.'
        )
      ) {
        await setMaintenanceMode(true, reason);
      }
    } else {
      await setMaintenanceMode(false);
    }
  };

  return (
    <div
      className={`p-6 rounded-2xl border shadow-xl backdrop-blur-md transition-all ${
        settings.maintenance_mode
          ? 'bg-amber-950/40 border-amber-500/60 shadow-amber-950/40'
          : 'bg-gray-900/80 border-gray-800'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-800 pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-xl ${
              settings.maintenance_mode ? 'bg-amber-500 text-gray-950 animate-bounce' : 'bg-gray-800 text-gray-300'
            }`}
          >
            <Wrench className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">System Maintenance Mode</h3>
            <p className="text-xs text-gray-400">
              Gracefully halt live accident ingestion during software upgrades
            </p>
          </div>
        </div>

        <button
          onClick={toggleMaintenance}
          disabled={isLoading}
          className={`px-5 py-2.5 rounded-xl text-xs font-extrabold tracking-wider uppercase transition shadow-lg flex items-center gap-2 ${
            settings.maintenance_mode
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
              : 'bg-amber-600 hover:bg-amber-500 text-gray-950 font-bold shadow-amber-600/30'
          }`}
        >
          {settings.maintenance_mode ? (
            <>
              <Play className="w-4 h-4 fill-white" />
              Resume Live Operations
            </>
          ) : (
            <>
              <Power className="w-4 h-4" />
              Activate Maintenance
            </>
          )}
        </button>
      </div>

      <div className="space-y-3">
        <div className="text-xs text-gray-300 leading-relaxed">
          {settings.maintenance_mode ? (
            <div className="p-3 bg-amber-950/60 border border-amber-600/40 rounded-xl text-amber-200">
              <strong>Status: ACTIVE</strong> — The system is currently in Maintenance Mode. Live camera accident monitoring is paused and all outgoing hospital emergency notifications are blocked. Historical data and audit logs remain accessible.
            </div>
          ) : (
            <p className="text-gray-400">
              Activating maintenance mode instructs the backend to reject non-admin incident submissions, pause scheduler repeats, and flag the system as unavailable to external responders.
            </p>
          )}
        </div>

        {!settings.maintenance_mode && (
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-1">
              Maintenance Reason (Logged for Audit)
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs focus:outline-none focus:border-amber-500"
            />
          </div>
        )}
      </div>
    </div>
  );
};
