import React, { useState, useEffect } from 'react';
import { useIncidents } from '../../context/IncidentContext';
import { useSettings } from '../../context/SettingsContext';
import { notificationApi } from '../../api/notificationApi';
import { Notification, Incident } from '../../types';
import {
  Bell,
  Clock,
  CheckCircle2,
  AlertOctagon,
  Phone,
  Send,
  RefreshCw,
  Building2,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';

export const NotificationQueue: React.FC = () => {
  const { incidents, stopIncidentNotifications } = useIncidents();
  const { settings } = useSettings();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('');
  const [countdown, setCountdown] = useState<number>(settings.notification_interval_seconds);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const activeIncidents = incidents.filter(
    (i) => i.status !== 'resolved' && i.status !== 'cancelled'
  );

  useEffect(() => {
    if (activeIncidents.length > 0 && !selectedIncidentId) {
      setSelectedIncidentId(activeIncidents[0].id);
    }
  }, [activeIncidents, selectedIncidentId]);

  const targetIncident = incidents.find((i) => i.id === selectedIncidentId);

  useEffect(() => {
    const fetchNotifs = async () => {
      setIsLoading(true);
      try {
        if (selectedIncidentId) {
          const res = await notificationApi.getIncidentNotifications(selectedIncidentId);
          setNotifications(res);
        } else {
          const res = await notificationApi.getAllNotifications();
          setNotifications(res);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchNotifs();
  }, [selectedIncidentId]);

  // Repeat interval countdown simulation
  useEffect(() => {
    if (!targetIncident || targetIncident.status === 'acknowledged' || targetIncident.status === 'resolved') {
      return;
    }

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          return settings.notification_interval_seconds;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [settings.notification_interval_seconds, targetIncident]);

  return (
    <div className="space-y-6">
      {/* Active Repeat Notification Procedure Card */}
      {targetIncident && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-gray-900 via-gray-900 to-gray-950 border border-gray-800 shadow-2xl backdrop-blur-md">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-5">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-sm font-bold text-white">
                  Incident: {targetIncident.incident_id}
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-purple-950 text-purple-400 border border-purple-800 animate-pulse flex items-center gap-1">
                  <Bell className="w-3 h-3" />
                  Active Notification Procedure
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Location: {targetIncident.location_description || 'Highway Corridor'}
              </p>
            </div>

            {targetIncident.status !== 'acknowledged' && targetIncident.status !== 'resolved' && (
              <button
                onClick={() => stopIncidentNotifications(targetIncident.id)}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-red-600/30 flex items-center gap-2 transition flex-shrink-0"
              >
                <AlertOctagon className="w-4 h-4" />
                Stop Messaging Procedure
              </button>
            )}
          </div>

          {/* Procedure Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5 text-xs font-mono">
            <div className="p-3.5 bg-gray-950/80 rounded-xl border border-gray-800">
              <p className="text-[10px] text-gray-400 uppercase">Repeat Interval</p>
              <p className="text-base font-bold text-white mt-0.5">
                {settings.notification_interval_seconds}s ({settings.notification_interval_seconds / 60}m)
              </p>
            </div>

            <div className="p-3.5 bg-gray-950/80 rounded-xl border border-gray-800">
              <p className="text-[10px] text-gray-400 uppercase">Next Scheduled Alert</p>
              <p className="text-base font-bold text-amber-400 mt-0.5 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {targetIncident.status === 'acknowledged' ? 'Halted (Ack Received)' : `in ${countdown}s`}
              </p>
            </div>

            <div className="p-3.5 bg-gray-950/80 rounded-xl border border-gray-800">
              <p className="text-[10px] text-gray-400 uppercase">Dispatches Sent</p>
              <p className="text-base font-bold text-emerald-400 mt-0.5">
                {targetIncident.notification_count || notifications.length} Attempts
              </p>
            </div>

            <div className="p-3.5 bg-gray-950/80 rounded-xl border border-gray-800">
              <p className="text-[10px] text-gray-400 uppercase">Acknowledgment</p>
              <p className="text-base font-bold text-purple-400 mt-0.5 capitalize">
                {targetIncident.acknowledged_at ? 'Received ✅' : 'Awaiting Hospital'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Incident Switcher & History Table */}
      <div className="p-6 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
            <Building2 className="w-5 h-5 text-purple-400" />
            Notification Audit & Dispatch Log
          </h3>

          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-400 font-medium">Filter Incident:</label>
            <select
              value={selectedIncidentId}
              onChange={(e) => setSelectedIncidentId(e.target.value)}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs font-mono focus:outline-none"
            >
              <option value="">All Incidents</option>
              {incidents.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.incident_id} ({i.severity.toUpperCase()})
                </option>
              ))}
            </select>
          </div>
        </div>

        {notifications.length === 0 ? (
          <p className="text-sm text-gray-500 py-8 text-center">No notification history recorded for this query.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-gray-950 text-gray-400 uppercase text-[10px] font-bold border-b border-gray-800">
                <tr>
                  <th className="px-4 py-3">Dispatch ID</th>
                  <th className="px-4 py-3">Recipient</th>
                  <th className="px-4 py-3">Channel</th>
                  <th className="px-4 py-3">Cycle #</th>
                  <th className="px-4 py-3">Delivery Status</th>
                  <th className="px-4 py-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {notifications.map((n) => (
                  <tr key={n.id} className="hover:bg-gray-800/40 transition">
                    <td className="px-4 py-3 font-bold text-white">{n.notification_id}</td>
                    <td className="px-4 py-3 text-gray-300">
                      <div>
                        <span className="font-sans font-semibold text-white">{n.recipient_name || 'Hospital Unit'}</span>
                        <p className="text-[10px] text-gray-400">{n.recipient_phone || '+919876543201'}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 uppercase font-bold text-blue-400">{n.notification_type}</td>
                    <td className="px-4 py-3 text-white">#{n.repeat_sequence || 1}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-950 text-emerald-400 border border-emerald-800">
                        {n.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {new Date(n.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
