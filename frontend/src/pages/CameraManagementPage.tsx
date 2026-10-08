import React, { useState } from 'react';
import { useCameras } from '../context/CameraContext';
import { useAuth } from '../context/AuthContext';
import { CameraCard } from '../components/cameras/CameraCard';
import { AddCameraModal } from '../components/cameras/AddCameraModal';
import { SystemCameraStream } from '../components/cameras/SystemCameraStream';
import { MobileCameraStream } from '../components/cameras/MobileCameraStream';
import {
  Cctv,
  Plus,
  Search,
  Filter,
  Video,
  Smartphone,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { CameraType } from '../types';

export const CameraManagementPage: React.FC = () => {
  const { cameras, onlineCount, offlineCount, monitoringCount } = useCameras();
  const { canManageCameras } = useAuth();

  const [search, setSearch] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);

  const filteredCameras = cameras.filter((c) => {
    const matchSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.camera_id.toLowerCase().includes(search.toLowerCase()) ||
      (c.location_name && c.location_name.toLowerCase().includes(search.toLowerCase()));

    if (!matchSearch) return false;
    if (typeFilter !== 'all' && c.camera_type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-wide">
            Highway Camera Infrastructure Management
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Register, configure, and monitor IP CCTV streams, USB workstations, and patrol mobile cameras
          </p>
        </div>

        {canManageCameras && (
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-red-600/30 flex items-center gap-2 transition flex-shrink-0"
          >
            <Plus className="w-4 h-4" />
            Register New Camera
          </button>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div>
            <p className="text-[11px] text-gray-400 uppercase">Total Camera Units</p>
            <p className="text-2xl font-bold text-white mt-0.5">{cameras.length}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-gray-800 text-gray-300">
            <Cctv className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div>
            <p className="text-[11px] text-gray-400 uppercase">Monitoring (Live AI)</p>
            <p className="text-2xl font-bold text-emerald-400 mt-0.5">{monitoringCount}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-emerald-950 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 flex items-center justify-between">
          <div>
            <p className="text-[11px] text-gray-400 uppercase">Disconnected / Error</p>
            <p className="text-2xl font-bold text-red-400 mt-0.5">{offlineCount}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-red-950 text-red-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Direct Capture Devices Hub (USB Webcam & Mobile Unit) */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-gray-300">
          Direct Ingestion Devices
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemCameraStream />
          <MobileCameraStream />
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-4 border-t border-gray-800">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search cameras by ID, name, location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900/90 border border-gray-800 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-medium">Filter Type:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 bg-gray-900 border border-gray-800 rounded-xl text-white text-xs font-semibold focus:outline-none"
          >
            <option value="all">All Camera Types</option>
            <option value="ip_cctv">External CCTV / IP Streams</option>
            <option value="system">System / USB Workstations</option>
            <option value="mobile">Patrol Mobile Units</option>
          </select>
        </div>
      </div>

      {/* Camera Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {filteredCameras.map((camera) => (
          <CameraCard key={camera.id} camera={camera} />
        ))}
      </div>

      {/* Add Camera Modal */}
      <AddCameraModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />
    </div>
  );
};
