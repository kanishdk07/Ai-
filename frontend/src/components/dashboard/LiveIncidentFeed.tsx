import React from 'react';
import { useIncidents } from '../../context/IncidentContext';
import { SeverityBadge } from '../common/SeverityBadge';
import { StatusBadge } from '../common/StatusBadge';
import { Incident } from '../../types';
import { AlertTriangle, Clock, MapPin, Eye, Car } from 'lucide-react';
import { PageId } from '../common/Sidebar';

interface LiveIncidentFeedProps {
  onSelectIncident: (id: string) => void;
  onNavigate?: (page: PageId) => void;
}

export const LiveIncidentFeed: React.FC<LiveIncidentFeedProps> = ({
  onSelectIncident,
  onNavigate,
}) => {
  const { incidents, selectIncidentById } = useIncidents();

  // Display top 6 most recent active/recent incidents
  const recentIncidents = [...incidents]
    .sort((a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime())
    .slice(0, 6);

  return (
    <div className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 backdrop-blur-md shadow-xl flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300">Live Incident Stream</h3>
          <p className="text-xs text-gray-400">Real-time incoming highway accident detections</p>
        </div>
        {onNavigate && (
          <button
            onClick={() => onNavigate('incidents')}
            className="text-xs font-bold text-red-400 hover:text-red-300 transition"
          >
            View All ({incidents.length}) →
          </button>
        )}
      </div>

      <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1">
        {recentIncidents.length === 0 ? (
          <div className="p-8 text-center text-gray-400 border border-dashed border-gray-800 rounded-xl">
            <AlertTriangle className="w-8 h-8 text-gray-600 mx-auto mb-2" />
            <p className="text-sm font-medium">No active accident incidents detected</p>
            <p className="text-xs text-gray-400 mt-1">Highway camera feeds are operating normally.</p>
          </div>
        ) : (
          recentIncidents.map((inc: Incident) => (
            <div
              key={inc.id}
              onClick={() => {
                selectIncidentById(inc.id);
                onSelectIncident(inc.id);
              }}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                inc.severity === 'high' && inc.status !== 'resolved'
                  ? 'bg-red-950/20 border-red-500/40 hover:bg-red-950/30'
                  : 'bg-gray-800/60 border-gray-700/60 hover:bg-gray-800'
              }`}
            >
              <div className="flex items-start gap-3 min-w-0">
                <div className="w-16 h-14 rounded-lg overflow-hidden flex-shrink-0 bg-gray-950 border border-gray-700 relative">
                  {inc.accident_image_url ? (
                    <img
                      src={inc.accident_image_url}
                      alt="Accident snapshot"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-600">
                      <Car className="w-5 h-5" />
                    </div>
                  )}
                  <span className="absolute bottom-0 inset-x-0 bg-black/70 text-[9px] text-center font-mono text-gray-300">
                    {Math.round(inc.confidence_score * 100)}% AI
                  </span>
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs font-bold text-white">{inc.incident_id}</span>
                    <SeverityBadge severity={inc.severity} pulse={inc.status !== 'resolved'} />
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-gray-300 mt-1 truncate">
                    <MapPin className="w-3 h-3 text-red-400 flex-shrink-0" />
                    <span className="truncate">{inc.location_description || 'Highway Corridor'}</span>
                  </div>

                  <div className="flex items-center gap-3 text-[11px] text-gray-400 mt-1 font-mono">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(inc.detected_at).toLocaleTimeString()}
                    </span>
                    <span>• {inc.vehicle_count || 1} Vehicle(s)</span>
                  </div>
                </div>
              </div>

              <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 flex-shrink-0">
                <StatusBadge status={inc.status} />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    selectIncidentById(inc.id);
                    onSelectIncident(inc.id);
                  }}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                >
                  <Eye className="w-3 h-3" />
                  Inspect
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
