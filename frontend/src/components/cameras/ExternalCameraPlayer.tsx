import React, { useState } from 'react';
import { Camera, Incident } from '../../types';
import { BoundingBoxCanvas } from '../monitoring/BoundingBoxCanvas';
import {
  Maximize2,
  Minimize2,
  Radio,
  Play,
  Square,
  AlertTriangle,
  Layers,
  MapPin,
  HeartPulse,
} from 'lucide-react';
import { useCameras } from '../../context/CameraContext';

interface ExternalCameraPlayerProps {
  camera: Camera;
  activeIncident?: Incident | null;
  expanded?: boolean;
  onToggleExpand?: () => void;
  onSelectCamera?: (camera: Camera) => void;
}

export const ExternalCameraPlayer: React.FC<ExternalCameraPlayerProps> = ({
  camera,
  activeIncident,
  expanded = false,
  onToggleExpand,
  onSelectCamera,
}) => {
  const { startMonitoring, stopMonitoring } = useCameras();
  const [showAiOverlay, setShowAiOverlay] = useState<boolean>(true);

  const streamSrc =
    camera.connection_config?.stream_endpoint ||
    'https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80';

  const vehicles = activeIncident?.vehicle_info?.vehicles || [
    { type: 'Car (Sedan)', color: 'White', bbox: [0.2, 0.4, 0.28, 0.35], speed_kmh: 74, confidence: 0.94 },
    { type: 'Commercial Truck', color: 'Blue', bbox: [0.55, 0.3, 0.35, 0.5], speed_kmh: 62, confidence: 0.91 },
  ];

  return (
    <div
      onClick={() => onSelectCamera && onSelectCamera(camera)}
      className={`rounded-2xl bg-gray-900/90 border border-gray-800 shadow-2xl backdrop-blur-md overflow-hidden flex flex-col justify-between transition-all ${
        activeIncident && activeIncident.status !== 'resolved'
          ? 'border-red-600/60 shadow-red-950/40'
          : 'hover:border-gray-700'
      } ${expanded ? 'h-full' : ''}`}
    >
      {/* Header Info */}
      <div className="p-3.5 bg-gray-950/80 border-b border-gray-800 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
              camera.status === 'monitoring'
                ? 'bg-emerald-400 animate-pulse'
                : camera.status === 'online'
                ? 'bg-blue-400'
                : 'bg-red-500'
            }`}
          />
          <div className="min-w-0">
            <h4 className="text-xs font-bold text-white tracking-wide truncate">{camera.name}</h4>
            <p className="text-[10px] text-gray-400 font-mono truncate">{camera.camera_id}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {activeIncident && activeIncident.status !== 'resolved' && (
            <span className="px-2 py-0.5 rounded-md bg-red-950 text-red-400 border border-red-800 text-[10px] font-bold animate-pulse flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              CRASH
            </span>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowAiOverlay(!showAiOverlay);
            }}
            className={`p-1.5 rounded-lg border text-xs transition ${
              showAiOverlay
                ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-400'
                : 'bg-gray-800 border-gray-700 text-gray-400'
            }`}
            title="Toggle AI Bounding Box Annotations"
          >
            <Layers className="w-3.5 h-3.5" />
          </button>

          {onToggleExpand && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleExpand();
              }}
              className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg border border-gray-700 transition"
              title={expanded ? 'Minimize Feed' : 'Expand Feed'}
            >
              {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Video / Bounding Box Viewport */}
      <div className="relative aspect-video w-full bg-gray-950 overflow-hidden flex items-center justify-center">
        {camera.status === 'offline' ? (
          <div className="text-center p-6 text-gray-500">
            <Radio className="w-10 h-10 text-red-500 mx-auto mb-2 opacity-50" />
            <p className="text-xs font-bold text-red-400 uppercase tracking-wider">Feed Disconnected</p>
            <p className="text-[11px] text-gray-400 mt-1">RTSP Stream connection unreachable</p>
          </div>
        ) : showAiOverlay ? (
          <BoundingBoxCanvas
            imageSrc={streamSrc}
            vehicles={vehicles}
            hasAccident={Boolean(activeIncident && activeIncident.status !== 'resolved')}
            severity={activeIncident?.severity || 'high'}
            confidenceScore={activeIncident?.confidence_score || 0.94}
          />
        ) : (
          <img src={streamSrc} alt={camera.name} className="w-full h-full object-cover" />
        )}

        {/* Live Stream Telemetry Stamp */}
        <div className="absolute bottom-2 left-2 flex items-center gap-2 px-2 py-0.5 bg-black/75 backdrop-blur-sm rounded text-[10px] font-mono text-gray-300 pointer-events-none">
          <span className="text-emerald-400">● 1080p 30fps</span>
          <span>|</span>
          <span className="truncate max-w-[140px]">{camera.location_name || 'Highway'}</span>
        </div>
      </div>

      {/* Footer Controls & Stats */}
      <div className="p-3 bg-gray-950/60 border-t border-gray-800 flex items-center justify-between text-xs">
        <div className="flex items-center gap-3 text-gray-400 font-mono text-[11px]">
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3 text-red-400" />
            {camera.latitude?.toFixed(2)}, {camera.longitude?.toFixed(2)}
          </span>
          <span className="flex items-center gap-1">
            <HeartPulse className="w-3 h-3 text-emerald-400" />
            {camera.health_score || 95}%
          </span>
        </div>

        <div>
          {camera.is_monitoring ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                stopMonitoring(camera.id);
              }}
              className="px-2.5 py-1 bg-red-950/80 hover:bg-red-900 border border-red-700/60 text-red-300 rounded-lg text-[11px] font-bold flex items-center gap-1 transition"
            >
              <Square className="w-3 h-3 fill-red-300" />
              Stop AI
            </button>
          ) : (
            <button
              onClick={(e) => {
                e.stopPropagation();
                startMonitoring(camera.id);
              }}
              className="px-2.5 py-1 bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700/60 text-emerald-300 rounded-lg text-[11px] font-bold flex items-center gap-1 transition"
            >
              <Play className="w-3.5 h-3.5 fill-emerald-300" />
              Start AI
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
