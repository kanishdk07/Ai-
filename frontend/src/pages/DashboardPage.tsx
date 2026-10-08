import React from 'react';
import { StatsOverview } from '../components/dashboard/StatsOverview';
import { SeverityChart } from '../components/dashboard/SeverityChart';
import { IncidentTimelineChart } from '../components/dashboard/IncidentTimelineChart';
import { LiveIncidentFeed } from '../components/dashboard/LiveIncidentFeed';
import { useCameras } from '../context/CameraContext';
import { ExternalCameraPlayer } from '../components/cameras/ExternalCameraPlayer';
import { PageId } from '../components/common/Sidebar';
import { Cctv, Video } from 'lucide-react';

interface DashboardPageProps {
  onNavigate: (page: PageId) => void;
  onSelectIncident: (id: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigate,
  onSelectIncident,
}) => {
  const { cameras } = useCameras();

  const monitoringCams = cameras.filter((c) => c.camera_type === 'ip_cctv').slice(0, 2);

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Welcome & Summary Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
            Highway Emergency Operations Dashboard
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Real-time optical surveillance, AI collision detection, and automated hospital dispatches
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('monitoring')}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-xl uppercase tracking-wider shadow-lg shadow-red-600/30 flex items-center gap-2 transition"
          >
            <Video className="w-4 h-4" />
            Live AI Camera Wall
          </button>
        </div>
      </div>

      {/* Primary KPI Metrics */}
      <StatsOverview onNavigate={onNavigate} />

      {/* Middle Grid: Live Incidents & Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <LiveIncidentFeed onSelectIncident={onSelectIncident} onNavigate={onNavigate} />
        </div>
        <div className="lg:col-span-5">
          <SeverityChart />
        </div>
      </div>

      {/* Bottom Grid: Timeline Velocity & High-Priority Camera Streams */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <IncidentTimelineChart />
        </div>
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
              <Cctv className="w-4 h-4 text-emerald-400" />
              Surveillance Grid Feed
            </h3>
            <button
              onClick={() => onNavigate('cameras')}
              className="text-xs font-bold text-red-400 hover:text-red-300"
            >
              Manage All Cameras →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {monitoringCams.map((cam) => (
              <ExternalCameraPlayer
                key={cam.id}
                camera={cam}
                onSelectCamera={() => onNavigate('monitoring')}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
