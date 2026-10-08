import React from 'react';
import { Incident } from '../../types';
import { SeverityBadge } from '../common/SeverityBadge';
import { StatusBadge } from '../common/StatusBadge';
import { Eye, MapPin, Clock, Car, AlertTriangle } from 'lucide-react';

interface IncidentTableProps {
  incidents: Incident[];
  onSelectIncident: (id: string) => void;
}

export const IncidentTable: React.FC<IncidentTableProps> = ({ incidents, onSelectIncident }) => {
  if (incidents.length === 0) {
    return (
      <div className="p-12 text-center text-gray-400 bg-gray-900/60 border border-gray-800 rounded-2xl">
        <AlertTriangle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
        <p className="text-base font-semibold text-gray-200">No Incidents Found</p>
        <p className="text-xs text-gray-500 mt-1">No accident events match your current filter criteria.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl overflow-hidden backdrop-blur-md">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-950/80 text-gray-400 uppercase text-[11px] font-bold tracking-wider border-b border-gray-800">
            <tr>
              <th className="px-5 py-3.5">Incident ID</th>
              <th className="px-5 py-3.5">Severity</th>
              <th className="px-5 py-3.5">Status</th>
              <th className="px-5 py-3.5">Location</th>
              <th className="px-5 py-3.5">Detected At</th>
              <th className="px-5 py-3.5">Vehicles / AI Conf.</th>
              <th className="px-5 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {incidents.map((inc) => (
              <tr
                key={inc.id}
                onClick={() => onSelectIncident(inc.id)}
                className="hover:bg-gray-800/50 cursor-pointer transition"
              >
                <td className="px-5 py-4 font-mono font-bold text-white whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="text-red-400">●</span>
                    {inc.incident_id}
                  </div>
                </td>
                <td className="px-5 py-4 whitespace-nowrap">
                  <SeverityBadge severity={inc.severity} pulse={inc.status !== 'resolved'} />
                </td>
                <td className="px-5 py-4 whitespace-nowrap">
                  <StatusBadge status={inc.status} />
                </td>
                <td className="px-5 py-4 max-w-xs truncate text-gray-300">
                  <div className="flex items-center gap-1.5 truncate">
                    <MapPin className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                    <span className="truncate">{inc.location_description || 'Highway Corridor'}</span>
                  </div>
                </td>
                <td className="px-5 py-4 font-mono text-xs text-gray-400 whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-gray-500" />
                    {new Date(inc.detected_at).toLocaleString()}
                  </div>
                </td>
                <td className="px-5 py-4 text-xs font-mono text-gray-300 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1">
                      <Car className="w-3.5 h-3.5 text-gray-400" />
                      {inc.vehicle_count || 1}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-gray-800 text-[11px] font-bold text-emerald-400">
                      {Math.round(inc.confidence_score * 100)}%
                    </span>
                  </div>
                </td>
                <td className="px-5 py-4 text-right whitespace-nowrap">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectIncident(inc.id);
                    }}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 hover:text-white rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 transition border border-gray-700"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Inspect
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
