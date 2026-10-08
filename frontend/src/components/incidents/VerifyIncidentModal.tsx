import React, { useState } from 'react';
import { Incident } from '../../types';
import { useIncidents } from '../../context/IncidentContext';
import { X, CheckCircle, AlertTriangle, ShieldAlert } from 'lucide-react';

interface VerifyIncidentModalProps {
  incident: Incident;
  isOpen: boolean;
  onClose: () => void;
}

export const VerifyIncidentModal: React.FC<VerifyIncidentModalProps> = ({
  incident,
  isOpen,
  onClose,
}) => {
  const { verifyIncident } = useIncidents();
  const [notes, setNotes] = useState<string>(
    'Confirmed high-speed collision on highway corridor. Visual verification complete.'
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await verifyIncident(incident.id, notes);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md bg-gray-900 border border-emerald-500/50 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 bg-emerald-950/60 border-b border-emerald-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-600 rounded-lg text-white">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Confirm Accident Incident</h3>
              <p className="text-xs text-emerald-300 font-mono">{incident.incident_id}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-xs text-emerald-300">
            Confirming this accident will validate the AI detection and transition the incident to <strong>ACTIVE</strong> status, prompting immediate emergency response dispatch.
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Verification Notes & Operator Rationale
            </label>
            <textarea
              required
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
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
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-emerald-600/30 transition disabled:opacity-50 flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              {isSubmitting ? 'Confirming...' : 'Confirm & Validate Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
