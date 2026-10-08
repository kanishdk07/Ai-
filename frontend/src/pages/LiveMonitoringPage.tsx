import React, { useState } from 'react';
import { useCameras } from '../context/CameraContext';
import { useIncidents } from '../context/IncidentContext';
import { ExternalCameraPlayer } from '../components/cameras/ExternalCameraPlayer';
import { SystemCameraStream } from '../components/cameras/SystemCameraStream';
import { MobileCameraStream } from '../components/cameras/MobileCameraStream';
import { Camera, Incident } from '../types';
import {
  Video,
  Cctv,
  Smartphone,
  Layers,
  AlertTriangle,
  Radio,
  Eye,
  CheckCircle,
} from 'lucide-react';

interface LiveMonitoringPageProps {
  onSelectIncident: (id: string) => void;
}

export const LiveMonitoringPage: React.FC<LiveMonitoringPageProps> = ({ onSelectIncident }) => {
  const { cameras } = useCameras();
  const { incidents } = useIncidents();

  const [activeTab, setActiveTab] = useState<'all' | 'ip_cctv' | 'system' | 'mobile'>('all');
  const [expandedCameraId, setExpandedCameraId] = useState<string | null>(null);

  const activeIncidents = incidents.filter(
    (i) => i.status !== 'resolved' && i.status !== 'cancelled'
  );

  const filteredCameras = cameras.filter((c) => {
    if (activeTab === 'all') return true;
    return c.camera_type === activeTab;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Header & Feed Filter Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
            <h1 className="text-xl font-extrabold text-white tracking-wide">
              Live Highway AI Monitoring Wall
            </h1>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Real-time multi-camera streams with YOLO-v9 vehicle detection & collision tracking
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-gray-950 rounded-xl border border-gray-800">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              activeTab === 'all'
                ? 'bg-red-600 text-white shadow-sm shadow-red-600/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            All Streams ({cameras.length})
          </button>
          <button
            onClick={() => setActiveTab('ip_cctv')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 ${
              activeTab === 'ip_cctv'
                ? 'bg-red-600 text-white shadow-sm shadow-red-600/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Cctv className="w-3.5 h-3.5" />
            Highway CCTV
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 ${
              activeTab === 'system'
                ? 'bg-red-600 text-white shadow-sm shadow-red-600/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            USB Webcam
          </button>
          <button
            onClick={() => setActiveTab('mobile')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 ${
              activeTab === 'mobile'
                ? 'bg-red-600 text-white shadow-sm shadow-red-600/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            Patrol Mobile
          </button>
        </div>
      </div>

      {/* Unconfirmed Incidents Alert Banner */}
      {activeIncidents.length > 0 && (
        <div className="p-4 rounded-2xl bg-red-950/40 border border-red-500/60 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-radar">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-600 rounded-xl text-white animate-bounce">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">
                {activeIncidents.length} Potential Crash Event(s) In Progress!
              </p>
              <p className="text-xs text-red-300">
                AI has detected anomalous vehicle impact. Operators must inspect and verify live footage.
              </p>
            </div>
          </div>

          <button
            onClick={() => onSelectIncident(activeIncidents[0].id)}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-red-600/30 flex items-center gap-1.5 transition flex-shrink-0"
          >
            <Eye className="w-4 h-4" />
            Inspect Critical Event ({activeIncidents[0].incident_id})
          </button>
        </div>
      )}

      {/* Special Direct Streams Section (USB / Mobile) */}
      {(activeTab === 'all' || activeTab === 'system') && (
        <div className="grid grid-cols-1 gap-6">
          <SystemCameraStream />
        </div>
      )}

      {(activeTab === 'all' || activeTab === 'mobile') && (
        <div className="grid grid-cols-1 gap-6">
          <MobileCameraStream />
        </div>
      )}

      {/* CCTV Cameras Grid View */}
      {(activeTab === 'all' || activeTab === 'ip_cctv') && (
        <div className="space-y-4">
          <h2 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
            <Cctv className="w-5 h-5 text-emerald-400" />
            Highway Optical PTZ Feeds ({cameras.filter((c) => c.camera_type === 'ip_cctv').length})
          </h2>

          <div
            className={`grid gap-6 ${
              expandedCameraId
                ? 'grid-cols-1'
                : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3'
            }`}
          >
            {filteredCameras
              .filter((c) => c.camera_type === 'ip_cctv')
              .map((cam: Camera) => {
                const camIncident = incidents.find(
                  (i) => i.camera_external_id === cam.camera_id || i.camera_id === cam.id
                );

                return (
                  <ExternalCameraPlayer
                    key={cam.id}
                    camera={cam}
                    activeIncident={camIncident}
                    expanded={expandedCameraId === cam.id}
                    onToggleExpand={() =>
                      setExpandedCameraId(expandedCameraId === cam.id ? null : cam.id)
                    }
                  />
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
};
