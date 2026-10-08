import React, { useState, useRef } from 'react';
import { Smartphone, SwitchCamera, Play, Square, Radio, AlertCircle } from 'lucide-react';
import { useCameras } from '../../context/CameraContext';

export const MobileCameraStream: React.FC = () => {
  const { cameras, startMonitoring, stopMonitoring } = useCameras();
  const mobileCam = cameras.find((c) => c.camera_type === 'mobile');

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const startMobileCamera = async () => {
    setError(null);
    try {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }

      const constraints: MediaStreamConstraints = {
        video: { facingMode: { ideal: facingMode }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);
      setIsStreaming(true);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }

      if (mobileCam) {
        await startMonitoring(mobileCam.id);
      }
    } catch (err: any) {
      setIsStreaming(false);
      setError(
        err?.name === 'NotAllowedError'
          ? 'Mobile camera permission denied. Please grant camera access.'
          : err?.message || 'Could not access mobile camera.'
      );
    }
  };

  const stopMobileCamera = async () => {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      setStream(null);
    }
    setIsStreaming(false);
    if (mobileCam) {
      await stopMonitoring(mobileCam.id);
    }
  };

  const toggleFacingMode = async () => {
    const nextMode = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(nextMode);
    if (isStreaming) {
      await stopMobileCamera();
      // will restart with nextMode
      setTimeout(() => startMobileCamera(), 300);
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-gray-900/90 border border-gray-800 shadow-2xl backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-purple-600/20 text-purple-400 rounded-xl">
            <Smartphone className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide">Patrol Mobile Unit Stream</h3>
            <p className="text-xs text-gray-400">Field response mobile camera streaming to AI detection server</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleFacingMode}
            className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition border border-gray-700"
            title="Switch Rear/Front Camera"
          >
            <SwitchCamera className="w-4 h-4 text-purple-400" />
            <span className="hidden sm:inline capitalize">{facingMode} Cam</span>
          </button>

          {!isStreaming ? (
            <button
              onClick={startMobileCamera}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-purple-600/30 flex items-center gap-2 transition"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              Stream Field Feed
            </button>
          ) : (
            <button
              onClick={stopMobileCamera}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-red-600/30 flex items-center gap-2 transition"
            >
              <Square className="w-3.5 h-3.5 fill-white" />
              End Stream
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3.5 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Video Viewport */}
      <div className="relative aspect-video w-full bg-gray-950 rounded-xl overflow-hidden border border-gray-800 flex items-center justify-center">
        {isStreaming ? (
          <>
            <video ref={videoRef} playsInline autoPlay muted className="w-full h-full object-cover" />
            <div className="absolute top-3 left-3 flex items-center gap-2 px-2.5 py-1 bg-black/70 backdrop-blur-md rounded-lg border border-white/10 text-[11px] font-mono text-purple-400">
              <Radio className="w-3 h-3 text-red-500 animate-pulse" />
              <span>MOBILE PATROL UPLINK</span>
            </div>
            <div className="absolute bottom-3 left-3 px-2.5 py-1 bg-black/70 backdrop-blur-md rounded-lg border border-white/10 text-[11px] font-mono text-gray-300">
              Transport: WebRTC / Secure AI Ingestion
            </div>
          </>
        ) : (
          <div className="text-center p-8">
            <Smartphone className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-sm font-semibold text-gray-300">Mobile Stream Inactive</p>
            <p className="text-xs text-gray-500 mt-1 max-w-sm">
              Launch field surveillance using mobile rear or front camera with secure transport.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
