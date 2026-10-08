import React, { useRef, useEffect } from 'react';
import { VehicleDetails } from '../../types';

interface BoundingBoxCanvasProps {
  imageSrc?: string;
  vehicles?: VehicleDetails[];
  hasAccident?: boolean;
  severity?: 'high' | 'medium' | 'low';
  confidenceScore?: number;
  className?: string;
}

export const BoundingBoxCanvas: React.FC<BoundingBoxCanvasProps> = ({
  imageSrc,
  vehicles = [],
  hasAccident = false,
  severity = 'high',
  confidenceScore = 0.92,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageSrc || 'https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80';

    img.onload = () => {
      canvas.width = img.naturalWidth || 800;
      canvas.height = img.naturalHeight || 450;

      // Draw original image
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      const w = canvas.width;
      const h = canvas.height;

      // Draw vehicle bounding boxes
      vehicles.forEach((v, index) => {
        const bbox = v.bbox || [0.2 + index * 0.25, 0.3, 0.25, 0.35];
        const [xNorm, yNorm, wNorm, hNorm] = bbox;

        const vx = xNorm * w;
        const vy = yNorm * h;
        const vw = wNorm * w;
        const vh = hNorm * h;

        const isCollisionTarget = hasAccident && index === 0;

        // Bounding Box stroke
        ctx.lineWidth = isCollisionTarget ? 4 : 2;
        ctx.strokeStyle = isCollisionTarget
          ? severity === 'high'
            ? '#EF4444'
            : severity === 'medium'
            ? '#F59E0B'
            : '#3B82F6'
          : '#10B981';

        ctx.strokeRect(vx, vy, vw, vh);

        // Tag label background
        const label = `${v.type || 'Vehicle'} • ${Math.round((v.confidence || confidenceScore) * 100)}%`;
        ctx.font = 'bold 14px Inter, sans-serif';
        const textWidth = ctx.measureText(label).width;

        ctx.fillStyle = isCollisionTarget
          ? severity === 'high'
            ? 'rgba(239, 68, 68, 0.9)'
            : 'rgba(245, 158, 11, 0.9)'
          : 'rgba(16, 185, 129, 0.9)';

        ctx.fillRect(vx, vy - 24, textWidth + 12, 24);

        // Label text
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(label, vx + 6, vy - 7);

        // Speed indicator tag if present
        if (v.speed_kmh !== undefined) {
          const speedLabel = `${v.speed_kmh} km/h`;
          ctx.font = '12px Inter, sans-serif';
          const speedWidth = ctx.measureText(speedLabel).width;
          ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
          ctx.fillRect(vx, vy + vh + 2, speedWidth + 8, 20);
          ctx.fillStyle = '#E5E7EB';
          ctx.fillText(speedLabel, vx + 4, vy + vh + 16);
        }
      });

      // Draw overall crash indicator if accident detected
      if (hasAccident) {
        ctx.fillStyle = severity === 'high' ? '#EF4444' : '#F59E0B';
        ctx.font = 'bold 18px Outfit, sans-serif';
        const crashText = `CRASH DETECTED (${Math.round(confidenceScore * 100)}% CONFIDENCE)`;
        const txtWidth = ctx.measureText(crashText).width;

        ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
        ctx.fillRect(16, 16, txtWidth + 24, 36);
        ctx.strokeStyle = severity === 'high' ? '#EF4444' : '#F59E0B';
        ctx.lineWidth = 2;
        ctx.strokeRect(16, 16, txtWidth + 24, 36);

        ctx.fillStyle = severity === 'high' ? '#EF4444' : '#F59E0B';
        ctx.fillText(crashText, 28, 41);
      }
    };
  }, [imageSrc, vehicles, hasAccident, severity, confidenceScore]);

  return (
    <div className={`relative w-full h-full overflow-hidden rounded-xl bg-gray-950 ${className}`}>
      <canvas ref={canvasRef} className="w-full h-full object-contain" />
    </div>
  );
};
