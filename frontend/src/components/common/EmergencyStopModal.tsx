import React, { useState } from 'react';
import { AlertOctagon, X, CheckCircle2 } from 'lucide-react';
import { useIncidents } from '../../context/IncidentContext';
import { useSettings } from '../../context/SettingsContext';

interface EmergencyStopModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultIncidentId?: string;
}

export const EmergencyStopModal: React.FC<EmergencyStopModalProps> = ({
  isOpen,
  onClose,
  defaultIncidentId,
}) => {
  const { incidents, stopIncidentNotifications } = useIncidents();
  const { emergencyStopAll } = useSettings();
  
  const [scope, setScope] = useState<'single' | 'all'>(defaultIncidentId ? 'single' : 'all');
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>(defaultIncidentId || incidents[0]?.id || '');
  const [reason, setReason] = useState<string>('Emergency Halt Triggered by Authorized Operator');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setResult(null);

    try {
      if (scope === 'all') {
        const res = await emergencyStopAll(reason);
        setResult({
          success: true,
          message: `Global Emergency Stop Executed: ${res.message} (${res.stopped_count} notification cycles halted).`,
        });
      } else {
        await stopIncidentNotifications(selectedIncidentId, reason);
        setResult({
          success: true,
          message: `Emergency notifications halted for Incident ID ${selectedIncidentId}. Historical logs preserved.`,
        });
      }
    } catch (err: any) {
      setResult({
        success: false,
        message: err?.message || 'Failed to execute emergency stop on backend.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-gray-900 border-2 border-red-600 rounded-2xl shadow-2xl shadow-red-900/50 overflow-hidden">
        {/* Header Strip */}
        <div className="flex items-center justify-between px-6 py-4 bg-red-950/60 border-b border-red-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-600 rounded-lg text-white animate-pulse">
              <AlertOctagon className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-wide">EMERGENCY STOP CONTROL</h3>
              <p className="text-xs text-red-300 font-mono">CRITICAL SAFETY OVERRIDE</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {result ? (
            <div className={`p-4 rounded-xl border flex items-start gap-3 ${
              result.success ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300' : 'bg-red-950/40 border-red-500/40 text-red-300'
            }`}>
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">{result.success ? 'Override Confirmed' : 'Action Failed'}</p>
                <p className="text-sm mt-1 text-slate-300">{result.message}</p>
                <button
                  type="button"
                  onClick={onClose}
                  className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold rounded-lg transition"
                >
                  Close Window
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="p-3 bg-red-950/30 border border-red-800/40 rounded-xl text-xs text-red-300 leading-relaxed">
                <strong>Attention:</strong> Triggering an Emergency Stop will immediately instruct the backend scheduler to halt pending and repeating SMS/call notification dispatches. Incident records and camera footage will remain safely archived in the database.
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-2">
                  Stop Scope
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setScope('single')}
                    className={`py-3 px-4 rounded-xl border text-sm font-semibold transition ${
                      scope === 'single'
                        ? 'bg-red-900/40 border-red-500 text-white shadow-lg'
                        : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-750'
                    }`}
                  >
                    Specific Incident
                  </button>
                  <button
                    type="button"
                    onClick={() => setScope('all')}
                    className={`py-3 px-4 rounded-xl border text-sm font-semibold transition ${
                      scope === 'all'
                        ? 'bg-red-600 border-red-400 text-white shadow-lg shadow-red-600/30'
                        : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-750'
                    }`}
                  >
                    Global System Halt
                  </button>
                </div>
              </div>

              {scope === 'single' && (
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                    Select Target Incident
                  </label>
                  <select
                    value={selectedIncidentId}
                    onChange={(e) => setSelectedIncidentId(e.target.value)}
                    className="w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
                  >
                    {incidents.map((inc) => (
                      <option key={inc.id} value={inc.id}>
                        {inc.incident_id} - {inc.severity.toUpperCase()} ({inc.location_description || 'Highway'})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                  Reason for Override (Audit Log)
                </label>
                <textarea
                  required
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
                  placeholder="State operational rationale..."
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl text-sm font-bold tracking-wide shadow-lg shadow-red-600/40 transition disabled:opacity-50 flex items-center gap-2"
                >
                  <AlertOctagon className="w-4 h-4" />
                  {isSubmitting ? 'Stopping...' : scope === 'all' ? 'EXECUTE GLOBAL STOP' : 'STOP INCIDENT ALERTS'}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
};
