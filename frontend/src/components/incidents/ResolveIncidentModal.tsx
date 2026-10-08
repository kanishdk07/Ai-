import React, { useState } from 'react';
import { Incident } from '../../types';
import { useIncidents } from '../../context/IncidentContext';
import { X, CheckCircle2 } from 'lucide-react';

interface ResolveIncidentModalProps {
  incident: Incident;
  isOpen: boolean;
  onClose: () => void;
}

export const ResolveIncidentModal: React.FC<ResolveIncidentModalProps> = ({
  incident,
  isOpen,
  onClose,
}) => {
  const { resolveIncident } = useIncidents();
  const [resolutionNotes, setResolutionNotes] = useState<string>(
    'Emergency medical team arrived on site. Victims stabilized and transported. Highway corridor cleared of wreckage and reopened.'
  );
  const [outcome, setOutcome] = useState<string>('successful');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await resolveIncident(incident.id, resolutionNotes, outcome);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-gray-900 border border-emerald-500/50 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 bg-emerald-950/60 border-b border-emerald-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-600 rounded-lg text-white">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Resolve & Close Incident</h3>
              <p className="text-xs text-emerald-300 font-mono">{incident.incident_id}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Resolution Outcome
            </label>
            <select
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
            >
              <option value="successful">Successful - All Victims Evacuated & Road Cleared</option>
              <option value="transferred">Transferred to Local Police & Fire Dept</option>
              <option value="minor">Minor Damage Only - Vehicles Self-Removed</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Resolution Summary & Clearance Log *
            </label>
            <textarea
              required
              rows={4}
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
              placeholder="Detail medical response, patient condition, and road restoration..."
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
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-emerald-600/30 transition disabled:opacity-50 flex items-center gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              {isSubmitting ? 'Resolving...' : 'Mark Resolved & Close Incident'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
