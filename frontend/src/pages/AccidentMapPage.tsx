import React from 'react';
import { AccidentMap } from '../components/map/AccidentMap';
import { MapPin, Info } from 'lucide-react';

interface AccidentMapPageProps {
  onSelectIncident: (id: string) => void;
}

export const AccidentMapPage: React.FC<AccidentMapPageProps> = ({ onSelectIncident }) => {
  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-red-500" />
            <h1 className="text-xl font-extrabold text-white tracking-wide">
              Interactive Highway Incident & Emergency Map
            </h1>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Real-time geospatial visualization of highway CCTV feeds, collision hotspots, and regional trauma centers
          </p>
        </div>
      </div>

      {/* Full-width Map Canvas */}
      <AccidentMap height="720px" onSelectIncident={onSelectIncident} />
    </div>
  );
};
