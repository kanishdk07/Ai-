import React, { useState } from 'react';
import { useIncidents } from '../../context/IncidentContext';
import { useCameras } from '../../context/CameraContext';
import { useWebSocket } from '../../context/WebSocketContext';
import { SeverityLevel } from '../../types';
import { X, Sparkles, AlertTriangle, Play, ShieldAlert } from 'lucide-react';

interface DemoSimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DemoSimulatorModal: React.FC<DemoSimulatorModalProps> = ({ isOpen, onClose }) => {
  const { createIncident } = useIncidents();
  const { cameras } = useCameras();
  const { simulateEvent } = useWebSocket();

  const [severity, setSeverity] = useState<SeverityLevel>('high');
  const [selectedCameraId, setSelectedCameraId] = useState<string>(cameras[0]?.camera_id || 'CAM-NH48-KM245');
  const [locationDescription, setLocationDescription] = useState<string>(
    'NH-48 KM 245 Toll Plaza North Merging Lane'
  );
  const [vehicleCount, setVehicleCount] = useState<number>(2);
  const [confidenceScore, setConfidenceScore] = useState<number>(0.95);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSimulating(true);

    const targetCam = cameras.find((c) => c.camera_id === selectedCameraId) || cameras[0];
    const incidentId = `ACC-SIM-${Date.now().toString().slice(-4)}`;

    const newIncidentData = {
      incident_id: incidentId,
      camera_id: targetCam?.id,
      camera_external_id: targetCam?.camera_id,
      detected_at: new Date().toISOString(),
      accident_detected: true,
      severity,
      confidence_score: confidenceScore,
      latitude: targetCam?.latitude || 28.4595,
      longitude: targetCam?.longitude || 77.0266,
      location_description: locationDescription,
      accident_image_url: 'https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80',
      status: 'detected' as const,
      vehicle_count: vehicleCount,
      vehicle_info: {
        vehicles: [
          { type: 'Commercial Vehicle', color: 'White', bbox: [0.15, 0.25, 0.45, 0.55], speed_kmh: 72, confidence: confidenceScore },
          { type: 'Sedan (Impact Target)', color: 'Silver', bbox: [0.45, 0.35, 0.35, 0.45], speed_kmh: 84, confidence: confidenceScore - 0.03 }
        ],
        total_vehicles: vehicleCount,
        estimated_impact_speed_kmh: 78
      },
      ai_event_data: {
        model_version: 'YOLO-v9-Accident-X',
        processing_time_ms: 128,
        collision_type: 'High-Speed Merging Collision',
        fire_detected: false,
        road_blockage: true
      }
    };

    try {
      const created = await createIncident(newIncidentData);
      simulateEvent('incident_created', created);
      onClose();
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-gray-900 border-2 border-purple-500/60 rounded-2xl shadow-2xl shadow-purple-950/60 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-purple-950/60 border-b border-purple-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-600 rounded-lg text-white animate-pulse">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Simulate Live AI Accident Event</h3>
              <p className="text-xs text-purple-300 font-mono">Test & Demonstration Toolkit</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSimulate} className="p-6 space-y-4">
          <div className="p-3 bg-purple-950/40 border border-purple-800/40 rounded-xl text-xs text-purple-200">
            This tool sends a simulated accident payload over WebSockets and the REST API to test immediate audio alerts, bounding box rendering, hospital radial search, and automated repeat notification schedules.
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Select Crash Severity *
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['high', 'medium', 'low'] as SeverityLevel[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSeverity(s)}
                  className={`py-2 px-3 rounded-xl border text-xs font-bold uppercase transition ${
                    severity === s
                      ? s === 'high'
                        ? 'bg-red-600 text-white border-red-500 shadow-md shadow-red-600/30'
                        : s === 'medium'
                        ? 'bg-amber-600 text-white border-amber-500 shadow-md shadow-amber-600/30'
                        : 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-600/30'
                      : 'bg-gray-800 text-gray-400 border-gray-700 hover:text-white'
                  }`}
                >
                  {s} Severity
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Surveillance Camera *
            </label>
            <select
              value={selectedCameraId}
              onChange={(e) => {
                setSelectedCameraId(e.target.value);
                const cam = cameras.find((c) => c.camera_id === e.target.value);
                if (cam?.location_name) setLocationDescription(cam.location_name);
              }}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500"
            >
              {cameras.map((c) => (
                <option key={c.id} value={c.camera_id}>
                  {c.name} ({c.camera_id})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Location Description
            </label>
            <input
              type="text"
              required
              value={locationDescription}
              onChange={(e) => setLocationDescription(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Vehicles Involved
              </label>
              <input
                type="number"
                min={1}
                max={6}
                value={vehicleCount}
                onChange={(e) => setVehicleCount(parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm font-mono focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                AI Confidence (0.0 - 1.0)
              </label>
              <input
                type="number"
                step="0.01"
                min={0.5}
                max={0.99}
                value={confidenceScore}
                onChange={(e) => setConfidenceScore(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm font-mono focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSimulating}
              className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-purple-600/30 transition disabled:opacity-50 flex items-center gap-2"
            >
              <Play className="w-4 h-4 fill-white" />
              {isSimulating ? 'Injecting...' : 'Inject Simulated Detection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
