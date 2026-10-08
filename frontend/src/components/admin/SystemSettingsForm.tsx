import React, { useState } from 'react';
import { useSettings } from '../../context/SettingsContext';
import { Sliders, Save, CheckCircle2, Bell, AlertTriangle } from 'lucide-react';

export const SystemSettingsForm: React.FC = () => {
  const { settings, updateSettings, isLoading } = useSettings();

  const [autoNotify, setAutoNotify] = useState<boolean>(settings.auto_notification_enabled);
  const [intervalSeconds, setIntervalSeconds] = useState<number>(settings.notification_interval_seconds);
  const [searchRadius, setSearchRadius] = useState<number>(settings.hospital_search_radius_km);
  const [maxHospitals, setMaxHospitals] = useState<number>(settings.max_hospitals_to_notify);
  const [maxRetries, setMaxRetries] = useState<number>(settings.max_notification_retries);
  const [testMode, setTestMode] = useState<boolean>(settings.test_mode);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateSettings({
      auto_notification_enabled: autoNotify,
      notification_interval_seconds: intervalSeconds,
      hospital_search_radius_km: searchRadius,
      max_hospitals_to_notify: maxHospitals,
      max_notification_retries: maxRetries,
      test_mode: testMode,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 4000);
  };

  return (
    <div className="p-6 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md space-y-6">
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-red-600/20 text-red-400 rounded-xl">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">Automated Emergency Alert Rules</h3>
            <p className="text-xs text-gray-400">Configure notification intervals, radius, and hospital limits</p>
          </div>
        </div>

        {savedSuccess && (
          <span className="px-3 py-1 bg-emerald-950 border border-emerald-500 text-emerald-400 text-xs font-bold rounded-lg flex items-center gap-1.5 animate-fadeIn">
            <CheckCircle2 className="w-4 h-4" />
            Saved & Confirmed by Backend
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Automatic Notification Toggle */}
        <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white">Automatic Hospital Notification Workflow</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  autoNotify
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                    : 'bg-amber-950 text-amber-400 border border-amber-800'
                }`}
              >
                {autoNotify ? 'AUTOMATIC ON' : 'MANUAL CONFIRMATION ONLY'}
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed max-w-xl">
              When <strong>ON</strong>, verified high & medium severity accidents automatically trigger repeat SMS/Call notifications to nearby hospitals at the configured interval until acknowledged. When <strong>OFF</strong>, notifications must be manually initiated by an operator.
            </p>
          </div>

          <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
            <input
              type="checkbox"
              checked={autoNotify}
              onChange={(e) => setAutoNotify(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
          </label>
        </div>

        {/* Repeat Interval Configuration (30s to 300s) */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-wider text-gray-300">
              Notification Repeat Interval (30s to 300s)
            </label>
            <span className="font-mono text-xs font-bold text-red-400 bg-red-950/60 px-2.5 py-1 rounded-md border border-red-800/40">
              {intervalSeconds} seconds ({intervalSeconds / 60} minutes)
            </span>
          </div>
          <input
            type="range"
            min={30}
            max={300}
            step={15}
            value={intervalSeconds}
            onChange={(e) => setIntervalSeconds(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-600"
          />
          <div className="flex justify-between text-[10px] font-mono text-gray-400 mt-1">
            <span>Minimum: 30s</span>
            <span>Default: 60s (1 min)</span>
            <span>Maximum: 300s (5 min)</span>
          </div>
        </div>

        {/* Search Radius & Max Hospitals */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Hospital Search Radius (km)
            </label>
            <input
              type="number"
              min={5}
              max={150}
              value={searchRadius}
              onChange={(e) => setSearchRadius(parseFloat(e.target.value))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm font-mono focus:outline-none focus:border-red-500"
            />
            <p className="text-[10px] text-gray-400 mt-1">PostGIS geographical radial query threshold</p>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Max Hospitals To Notify Per Incident
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={maxHospitals}
              onChange={(e) => setMaxHospitals(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm font-mono focus:outline-none focus:border-red-500"
            />
            <p className="text-[10px] text-gray-400 mt-1">Simultaneous hospital dispatches per cycle</p>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-800 flex items-center justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-red-600/30 transition disabled:opacity-50 flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {isLoading ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
};
