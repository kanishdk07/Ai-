import React, { useState } from 'react';
import { useIncidents } from '../context/IncidentContext';
import { IncidentTable } from '../components/incidents/IncidentTable';
import { Search, Filter, AlertTriangle, Radio } from 'lucide-react';
import { SeverityLevel, IncidentStatus } from '../types';

interface IncidentListPageProps {
  onSelectIncident: (id: string) => void;
}

export const IncidentListPage: React.FC<IncidentListPageProps> = ({ onSelectIncident }) => {
  const { incidents, filterStatus, setFilterStatus, filterSeverity, setFilterSeverity } = useIncidents();
  const [search, setSearch] = useState<string>('');

  const filteredIncidents = incidents.filter((inc) => {
    const matchSearch =
      inc.incident_id.toLowerCase().includes(search.toLowerCase()) ||
      (inc.location_description && inc.location_description.toLowerCase().includes(search.toLowerCase())) ||
      (inc.camera_external_id && inc.camera_external_id.toLowerCase().includes(search.toLowerCase()));

    if (!matchSearch) return false;
    if (filterStatus !== 'all' && inc.status !== filterStatus) return false;
    if (filterSeverity !== 'all' && inc.severity !== filterSeverity) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-white tracking-wide">
              Highway Accident Incident Registry
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-red-950 text-red-400 border border-red-800">
              {incidents.length} Total Events
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Complete lifecycle tracking, AI collision verification, and emergency dispatch logs
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 bg-gray-900/80 border border-gray-800 rounded-2xl">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by incident ID (e.g. ACC-2026), location, camera..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs focus:outline-none focus:border-red-500"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs font-semibold focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="detected">Detected (Unverified)</option>
            <option value="active">Active Verified</option>
            <option value="notified">Notified (Awaiting Ack)</option>
            <option value="acknowledged">Hospital Acknowledged</option>
            <option value="resolved">Resolved & Cleared</option>
            <option value="cancelled">Cancelled (False Alarm)</option>
          </select>

          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-xs font-semibold focus:outline-none"
          >
            <option value="all">All Severities</option>
            <option value="high">High Severity</option>
            <option value="medium">Medium Severity</option>
            <option value="low">Low Severity</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <IncidentTable incidents={filteredIncidents} onSelectIncident={onSelectIncident} />
    </div>
  );
};
