import React from 'react';
import { useIncidents } from '../context/IncidentContext';
import { IncidentDetailView } from '../components/incidents/IncidentDetailView';
import { AlertTriangle, ArrowLeft } from 'lucide-react';
import { PageId } from '../components/common/Sidebar';

interface IncidentDetailPageProps {
  incidentId: string;
  onBack: () => void;
  onNavigate: (page: PageId) => void;
}

export const IncidentDetailPage: React.FC<IncidentDetailPageProps> = ({
  incidentId,
  onBack,
  onNavigate,
}) => {
  const { incidents } = useIncidents();
  const incident = incidents.find((i) => i.id === incidentId || i.incident_id === incidentId);

  if (!incident) {
    return (
      <div className="p-12 text-center text-gray-400 bg-gray-900/60 border border-gray-800 rounded-2xl space-y-4">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto" />
        <h2 className="text-lg font-bold text-white">Incident Not Found</h2>
        <p className="text-xs text-gray-400">The requested incident ID could not be loaded.</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-xl text-xs font-semibold inline-flex items-center gap-2 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Return to Incident Registry
        </button>
      </div>
    );
  }

  return (
    <IncidentDetailView
      incident={incident}
      onBack={onBack}
      onOpenMap={() => onNavigate('map')}
    />
  );
};
