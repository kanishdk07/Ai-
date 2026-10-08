import React, { useState } from 'react';
import { Camera, CameraType } from '../../types';
import { useCameras } from '../../context/CameraContext';
import { X, Cctv, ShieldCheck } from 'lucide-react';

interface AddCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddCameraModal: React.FC<AddCameraModalProps> = ({ isOpen, onClose }) => {
  const { createCamera } = useCameras();

  const [cameraId, setCameraId] = useState<string>(`CAM-NH-${Math.floor(Math.random() * 900 + 100)}`);
  const [name, setName] = useState<string>('');
  const [cameraType, setCameraType] = useState<CameraType>('ip_cctv');
  const [locationName, setLocationName] = useState<string>('');
  const [latitude, setLatitude] = useState<number>(28.6139);
  const [longitude, setLongitude] = useState<number>(77.2090);
  const [rtspUrl, setRtspUrl] = useState<string>('');
  const [username, setUsername] = useState<string>('admin');
  const [password, setPassword] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await createCamera({
        camera_id: cameraId,
        name,
        camera_type: cameraType,
        location_name: locationName,
        latitude,
        longitude,
        description,
        connection_config: {
          rtsp_url: rtspUrl,
          username,
        },
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to register camera on backend.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-950 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-600/20 text-red-400 rounded-lg">
              <Cctv className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-wide">Register New Highway Camera</h3>
              <p className="text-xs text-gray-400 font-mono">Camera Infrastructure Ingestion</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Camera ID *
              </label>
              <input
                type="text"
                required
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Camera Type *
              </label>
              <select
                value={cameraType}
                onChange={(e) => setCameraType(e.target.value as CameraType)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
              >
                <option value="ip_cctv">External IP / CCTV Stream</option>
                <option value="system">System / USB Camera</option>
                <option value="mobile">Patrol Mobile Unit</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Camera Display Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g., NH-48 KM 245 Toll Plaza North"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Location Description
            </label>
            <input
              type="text"
              placeholder="e.g., NH-48 KM 245 (Delhi-Jaipur Expressway)"
              value={locationName}
              onChange={(e) => setLocationName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Latitude (WGS84)
              </label>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={(e) => setLatitude(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
                Longitude (WGS84)
              </label>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={(e) => setLongitude(parseFloat(e.target.value))}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500 font-mono"
              />
            </div>
          </div>

          {cameraType === 'ip_cctv' && (
            <div className="p-4 bg-gray-950/60 rounded-xl border border-gray-800 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
                <span>Encrypted RTSP Credentials</span>
              </div>
              <p className="text-[11px] text-gray-400">
                Stream credentials are encrypted using AES-256 on the backend and never exposed in frontend responses.
              </p>

              <div>
                <label className="block text-[11px] text-gray-300 font-medium mb-1">RTSP Stream URL</label>
                <input
                  type="text"
                  placeholder="rtsp://192.168.1.100:554/live/ch0"
                  value={rtspUrl}
                  onChange={(e) => setRtspUrl(e.target.value)}
                  className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-white text-xs font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] text-gray-300 font-medium mb-1">RTSP Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-white text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-gray-300 font-medium mb-1">RTSP Password</label>
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-white text-xs"
                  />
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-300 mb-1">
              Description & Notes
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:border-red-500"
              placeholder="Notes on highway lane orientation, lens zoom, etc."
            />
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
              disabled={isSubmitting}
              className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-red-600/30 transition disabled:opacity-50"
            >
              {isSubmitting ? 'Registering...' : 'Register Camera'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
