import React, { useState } from 'react';
import { Camera } from '../../types';
import { useCameras } from '../../context/CameraContext';
import { useAuth } from '../../context/AuthContext';
import { EditCameraModal } from './EditCameraModal';
import {
  Cctv,
  Smartphone,
  Video,
  Play,
  Square,
  Settings2,
  HeartPulse,
  Radio,
  MapPin,
  Clock,
} from 'lucide-react';

interface CameraCardProps {
  camera: Camera;
  onSelect?: (camera: Camera) => void;
}

export const CameraCard: React.FC<CameraCardProps> = ({ camera, onSelect }) => {
  const { startMonitoring, stopMonitoring } = useCameras();
  const { canManageCameras } = useAuth();
  const [isEditOpen, setIsEditOpen] = useState<boolean>(false);

  const getTypeIcon = () => {
    switch (camera.camera_type) {
      case 'system':
        return <Video className="w-4 h-4 text-blue-400" />;
      case 'mobile':
        return <Smartphone className="w-4 h-4 text-purple-400" />;
      default:
        return <Cctv className="w-4 h-4 text-emerald-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (camera.status) {
      case 'monitoring':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1 animate-pulse">
            <Radio className="w-2.5 h-2.5" />
            Monitoring
          </span>
        );
      case 'online':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-blue-950 text-blue-400 border border-blue-800">
            Online (Idle)
          </span>
        );
      case 'offline':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-red-950 text-red-400 border border-red-800">
            Disconnected
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-gray-800 text-gray-400">
            {camera.status}
          </span>
        );
    }
  };

  return (
    <>
      <div
        onClick={() => onSelect && onSelect(camera)}
        className="rounded-2xl bg-gray-900/80 border border-gray-800 hover:border-gray-700 backdrop-blur-md shadow-xl p-5 flex flex-col justify-between transition group cursor-pointer"
      >
        <div>
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="p-2 bg-gray-800 rounded-xl flex-shrink-0 group-hover:scale-105 transition">
                {getTypeIcon()}
              </div>
              <div className="min-w-0">
                <h4 className="text-sm font-bold text-white tracking-wide truncate group-hover:text-red-400 transition">
                  {camera.name}
                </h4>
                <p className="text-[11px] font-mono text-gray-400 truncate">{camera.camera_id}</p>
              </div>
            </div>
            {getStatusBadge()}
          </div>

          {/* Location & Desc */}
          <div className="space-y-1.5 text-xs text-gray-300 mb-4">
            <div className="flex items-center gap-1.5 text-gray-400 truncate">
              <MapPin className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
              <span className="truncate">{camera.location_name || 'Highway Corridor'}</span>
            </div>
            {camera.description && (
              <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed">
                {camera.description}
              </p>
            )}
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-3 gap-2 p-2.5 bg-gray-950/70 rounded-xl border border-gray-800/80 text-center text-xs mb-4">
            <div>
              <p className="text-[10px] text-gray-400 uppercase font-mono">Health</p>
              <p className="font-bold text-emerald-400 mt-0.5">{camera.health_score ?? 98}%</p>
            </div>
            <div>
              <p className="text-[10px] text-gray-400 uppercase font-mono">Detections</p>
              <p className="font-bold text-white mt-0.5">{camera.total_detections || 0}</p>
            </div>
            <div>
              <p className="text-[10px] text-gray-400 uppercase font-mono">Uptime</p>
              <p className="font-bold text-blue-400 mt-0.5">{camera.uptime_percentage ?? 99.5}%</p>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-800/80">
          <span className="text-[10px] font-mono text-gray-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Active: {camera.last_active_at ? new Date(camera.last_active_at).toLocaleTimeString() : 'Recent'}
          </span>

          <div className="flex items-center gap-1.5">
            {canManageCameras && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditOpen(true);
                }}
                className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs transition"
                title="Edit Camera Details"
              >
                <Settings2 className="w-3.5 h-3.5" />
              </button>
            )}

            {camera.is_monitoring ? (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  stopMonitoring(camera.id);
                }}
                className="px-3 py-1.5 bg-red-950/80 hover:bg-red-900 border border-red-800/60 text-red-300 rounded-lg text-xs font-bold flex items-center gap-1 transition shadow-sm"
              >
                <Square className="w-3 h-3 fill-red-300" />
                Stop
              </button>
            ) : (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  startMonitoring(camera.id);
                }}
                className="px-3 py-1.5 bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800/60 text-emerald-300 rounded-lg text-xs font-bold flex items-center gap-1 transition shadow-sm"
              >
                <Play className="w-3 h-3 fill-emerald-300" />
                Monitor
              </button>
            )}
          </div>
        </div>
      </div>

      {isEditOpen && (
        <EditCameraModal
          camera={camera}
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
        />
      )}
    </>
  );
};
