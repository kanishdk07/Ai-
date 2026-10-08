import React, { useState } from 'react';
import { useIncidents } from '../../context/IncidentContext';
import { Send, Phone, AlertCircle, CheckCircle2, Clock, User, ShieldAlert } from 'lucide-react';
import { Notification } from '../../types';

export const ManualContactForm: React.FC = () => {
  const { incidents, sendManualAlert } = useIncidents();

  const activeIncidents = incidents.filter((i) => i.status !== 'resolved' && i.status !== 'cancelled');

  const [selectedIncidentId, setSelectedIncidentId] = useState<string>(activeIncidents[0]?.id || '');
  const [phoneNumber, setPhoneNumber] = useState<string>('+919876543210');
  const [recipientName, setRecipientName] = useState<string>('');
  const [customMessage, setCustomMessage] = useState<string>(
    'URGENT EMERGENCY: Highway accident detected. Medical assistance required immediately.'
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [sentNotifications, setSentNotifications] = useState<Notification[]>([]);
  const [error, setError] = useState<string | null>(null);

  // E.164 international phone format validator (+ followed by 10-15 digits)
  const isPhoneValid = /^\+[1-9]\d{9,14}$/.test(phoneNumber.trim());

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPhoneValid) {
      setError('Please enter a valid international phone number in E.164 format (e.g. +919876543210).');
      return;
    }
    if (!selectedIncidentId) {
      setError('Please select an active incident.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const notif = await sendManualAlert(
        selectedIncidentId,
        phoneNumber.trim(),
        recipientName || 'External Emergency Doctor',
        customMessage
      );
      setSentNotifications((prev) => [notif, ...prev]);
    } catch (err: any) {
      setError(err?.message || 'Failed to dispatch manual emergency alert.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedIncident = incidents.find((i) => i.id === selectedIncidentId);

  return (
    <div className="p-6 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md space-y-5">
      <div className="flex items-center gap-3 border-b border-gray-800 pb-4">
        <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl">
          <Phone className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white tracking-wide">Manual Recipient Emergency Dispatch</h3>
          <p className="text-xs text-gray-400">
            Send immediate SMS notification to external EMTs, on-call doctors, or emergency units
          </p>
        </div>
      </div>

      <form onSubmit={handleSend} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
            Target Active Incident *
          </label>
          {activeIncidents.length === 0 ? (
            <p className="text-xs text-amber-400">No active incidents available to dispatch.</p>
          ) : (
            <select
              value={selectedIncidentId}
              onChange={(e) => setSelectedIncidentId(e.target.value)}
              className="w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500 font-mono"
            >
              {activeIncidents.map((inc) => (
                <option key={inc.id} value={inc.id}>
                  {inc.incident_id} - {inc.severity.toUpperCase()} ({inc.location_description || 'Highway'})
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Mobile Number (E.164 International Format) *
            </label>
            <input
              type="tel"
              required
              placeholder="+919876543210"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className={`w-full px-3 py-2 bg-gray-800 border rounded-xl text-white text-sm font-mono focus:outline-none ${
                isPhoneValid ? 'border-emerald-500/60' : 'border-gray-700 focus:border-red-500'
              }`}
            />
            <p className="text-[10px] text-gray-400 mt-1">Must start with country code (+91, +1, etc.)</p>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Recipient Name / Role
            </label>
            <input
              type="text"
              placeholder="e.g., Dr. Mehra (Head of Trauma)"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
            Emergency Dispatch Message *
          </label>
          <textarea
            required
            rows={3}
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
          />
        </div>

        {/* Confirmation Preview */}
        {selectedIncident && isPhoneValid && (
          <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800 text-xs text-gray-300 space-y-1 font-mono">
            <p className="text-[10px] uppercase font-bold text-gray-400">Dispatch Confirmation Preview:</p>
            <p>
              Incident: <span className="text-white font-bold">{selectedIncident.incident_id}</span> ({selectedIncident.location_description})
            </p>
            <p>
              Recipient: <span className="text-emerald-400 font-bold">{phoneNumber}</span> ({recipientName || 'External Unit'})
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting || !isPhoneValid || activeIncidents.length === 0}
          className="w-full py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl text-sm font-bold uppercase tracking-wider shadow-lg shadow-red-600/30 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Send className="w-4 h-4" />
          {isSubmitting ? 'Transmitting Alert via SMS Gateway...' : 'Send Emergency Message'}
        </button>
      </form>

      {/* Real-time Dispatch Tracker */}
      {sentNotifications.length > 0 && (
        <div className="pt-4 border-t border-gray-800">
          <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">
            Dispatched Messages & Acknowledgment Tracker
          </h4>
          <div className="space-y-2 font-mono text-xs">
            {sentNotifications.map((n) => (
              <div
                key={n.id}
                className="p-3 bg-gray-950 rounded-xl border border-gray-800 flex items-center justify-between gap-3"
              >
                <div>
                  <p className="font-bold text-white">{n.recipient_name || n.recipient_phone}</p>
                  <p className="text-[10px] text-gray-400 truncate">{n.message}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Delivered
                  </span>
                  <p className="text-[9px] text-gray-500 mt-0.5">{new Date(n.created_at).toLocaleTimeString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
