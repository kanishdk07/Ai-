import React, { useState, useRef, useEffect } from 'react';
import { Camera, CameraOff, Video, Play, Square, Settings2, RefreshCw, Radio } from 'lucide-react';
import { useCameras } from '../../context/CameraContext';

interface SystemCameraStreamProps {
  onCaptureFrame?: (dataUrl: string) => void;
}

export const SystemCameraStream: React.FC<SystemCameraStreamProps> = ({ onCaptureFrame }) => {
  const { cameras, startMonitoring, stopMonitoring } = useCameras();
  const systemCam = cameras.find((c) => c.camera_type === 'system');

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);
  const [fps, setFps] = useState<number>(30);

  // Load connected media devices
  useEffect(() => {
    const getDevices = async () => {
      try {
        if (!navigator.mediaDevices?.enumerateDevices) {
          setError('Browser mediaDevices API not supported on this browser.');
          return;
        }
        const devList = await navigator.mediaDevices.enumerateDevices();
        const videoDevs = devList.filter((d) => d.kind === 'videoinput');
        setDevices(videoDevs);
        if (videoDevs.length > 0 && !selectedDeviceId) {
          setSelectedDeviceId(videoDevs[0].deviceId);
        }
      } catch (err: any) {
        setError(err?.message || 'Failed to enumerate camera devices');
      }
    };

    getDevices();
  }, [selectedDeviceId]);

  const startCamera = async () => {
    setError(null);
    try {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }

      const constraints: MediaStreamConstraints = {
        video: selectedDeviceId ? { deviceId: { exact: selectedDeviceId } } : true,
        audio: false,
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);
      setPermissionGranted(true);
      setIsStreaming(true);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }

      if (systemCam) {
        await startMonitoring(systemCam.id);
      }
    } catch (err: any) {
      setPermissionGranted(false);
      setIsStreaming(false);
      setError(
        err?.name === 'NotAllowedError'
          ? 'Camera permission was denied. Please allow camera access in your browser.'
          : err?.message || 'Could not start system camera.'
      );
    }
  };

  const stopCamera = async () => {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      setStream(null);
    }
    setIsStreaming(false);
    if (systemCam) {
      await stopMonitoring(systemCam.id);
    }
  };

  // Draw simulated AI bounding box on live video frame
  useEffect(() => {
    let animationFrameId: number;
    let lastTime = performance.now();
    let frameCount = 0;

    const renderLoop = (time: number) => {
      frameCount++;
      if (time - lastTime >= 1000) {
        setFps(frameCount);
        frameCount = 0;
        lastTime = time;
      }

      if (canvasRef.current && videoRef.current && isStreaming) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx && videoRef.current.videoWidth) {
          canvasRef.current.width = videoRef.current.videoWidth;
          canvasRef.current.height = videoRef.current.videoHeight;

          // Draw live video onto canvas
          ctx.drawImage(videoRef.current, 0, 0);

          // Simulated real-time AI bounding box overlay
          const w = canvasRef.current.width;
          const h = canvasRef.current.height;

          ctx.strokeStyle = '#10B981';
          ctx.lineWidth = 3;
          ctx.strokeRect(w * 0.25, h * 0.35, w * 0.45, h * 0.4);

          ctx.fillStyle = '#10B981';
          ctx.font = 'bold 16px Inter, sans-serif';
          ctx.fillText('Target Vehicle (0.94)', w * 0.25 + 5, h * 0.35 - 8);
        }
      }
      animationFrameId = requestAnimationFrame(renderLoop);
    };

    if (isStreaming) {
      animationFrameId = requestAnimationFrame(renderLoop);
    }

    return () => cancelAnimationFrame(animationFrameId);
  }, [isStreaming]);

  return (
    <div className="p-6 rounded-2xl bg-gray-900/90 border border-gray-800 shadow-2xl backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl">
            <Camera className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">System / USB Workstation Camera</h3>
            <p className="text-xs text-gray-400">Direct USB or laptop web camera for live edge AI analysis</p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {devices.length > 0 && (
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              disabled={isStreaming}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-xl focus:outline-none focus:border-blue-500"
            >
              {devices.map((d, i) => (
                <option key={d.deviceId || i} value={d.deviceId}>
                  {d.label || `Camera Device #${i + 1}`}
                </option>
              ))}
            </select>
          )}

          {!isStreaming ? (
            <button
              onClick={startCamera}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              Start Monitoring
            </button>
          ) : (
            <button
              onClick={stopCamera}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-red-600/30 flex items-center gap-2 transition"
            >
              <Square className="w-3.5 h-3.5 fill-white" />
              Stop Feed
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center gap-2">
          <CameraOff className="w-4 h-4 text-red-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Video Viewport */}
      <div className="relative aspect-video w-full bg-gray-950 rounded-xl overflow-hidden border border-gray-800 flex items-center justify-center group">
        {/* Hidden video stream element feeding canvas */}
        <video ref={videoRef} playsInline muted className="hidden" />

        {isStreaming ? (
          <>
            <canvas ref={canvasRef} className="w-full h-full object-contain" />
            {/* Live HUD Overlay */}
            <div className="absolute top-3 left-3 flex items-center gap-2 px-2.5 py-1 bg-black/70 backdrop-blur-md rounded-lg border border-white/10 text-[11px] font-mono text-emerald-400">
              <Radio className="w-3 h-3 text-red-500 animate-pulse" />
              <span>LIVE USB FEED</span>
              <span className="text-gray-400">|</span>
              <span>{fps} FPS</span>
            </div>
            <div className="absolute top-3 right-3 px-2.5 py-1 bg-black/70 backdrop-blur-md rounded-lg border border-white/10 text-[11px] font-mono text-gray-300">
              AI Overlay: Active
            </div>
          </>
        ) : (
          <div className="text-center p-8">
            <CameraOff className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-sm font-semibold text-gray-300">USB Camera Standby</p>
            <p className="text-xs text-gray-500 mt-1 max-w-sm">
              Click &quot;Start Monitoring&quot; above to request browser camera permissions and begin live stream analysis.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
