import React, { useState } from 'react';
import { Incident } from '../../types';
import { useIncidents } from '../../context/IncidentContext';
import { X, AlertCircle } from 'lucide-react';

interface CancelIncidentModalProps {
  incident: Incident;
  isOpen: boolean;
  onClose: () => void;
}

export const CancelIncidentModal: React.FC<CancelIncidentModalProps> = ({
  incident,
  isOpen,
  onClose,
}) => {
  const { cancelIncident } = useIncidents();
  const [reason, setReason] = useState<string>('False positive - routine highway slowdown / shadow anomaly');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await cancelIncident(incident.id, reason);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 bg-gray-950 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-800 text-gray-300 rounded-lg">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Mark False Positive</h3>
              <p className="text-xs text-gray-400 font-mono">{incident.incident_id}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-gray-400">
            Cancelling this incident will log a false-alarm audit entry, stop automated hospital notification procedures, and clear the event from the active monitoring queue.
          </p>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Cancellation Reason *
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm font-medium transition"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-xl text-sm font-bold transition disabled:opacity-50"
            >
              {isSubmitting ? 'Cancelling...' : 'Confirm False Positive'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
