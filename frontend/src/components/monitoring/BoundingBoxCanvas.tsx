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

    const drawOverlay = (width: number, height: number) => {
      // Draw vehicle bounding boxes
      vehicles.forEach((v, index) => {
        const bbox = v.bbox || [0.2 + index * 0.25, 0.3, 0.25, 0.35];
        const [xNorm, yNorm, wNorm, hNorm] = bbox;

        const vx = xNorm * width;
        const vy = yNorm * height;
        const vw = wNorm * width;
        const vh = hNorm * height;

        const isCollisionTarget = hasAccident && index === 0;

        ctx.lineWidth = isCollisionTarget ? 4 : 2;
        ctx.strokeStyle = isCollisionTarget
          ? severity === 'high'
            ? '#EF4444'
            : severity === 'medium'
            ? '#F59E0B'
            : '#3B82F6'
          : '#10B981';

        ctx.strokeRect(vx, vy, vw, vh);

        const label = `${v.type || 'Vehicle'} • ${Math.round((v.confidence || confidenceScore) * 100)}%`;
        ctx.font = 'bold 14px Inter, sans-serif';
        const textWidth = ctx.measureText(label).width;

        ctx.fillStyle = isCollisionTarget
          ? severity === 'high'
            ? 'rgba(239, 68, 68, 0.9)'
            : 'rgba(245, 158, 11, 0.9)'
          : 'rgba(16, 185, 129, 0.9)';

        ctx.fillRect(vx, vy - 24, textWidth + 12, 24);
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(label, vx + 6, vy - 7);

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

      if (hasAccident) {
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

    const drawFallbackBackdrop = (w: number, h: number) => {
      canvas.width = w;
      canvas.height = h;

      // Deep dark gradient backdrop
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, '#0F172A');
      grad.addColorStop(1, '#1E293B');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // Perspective highway lines
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 2;

      ctx.beginPath();
      ctx.moveTo(w * 0.4, h * 0.4);
      ctx.lineTo(w * 0.1, h);
      ctx.moveTo(w * 0.6, h * 0.4);
      ctx.lineTo(w * 0.9, h);
      ctx.stroke();

      // Dashed lane lines
      ctx.setLineDash([12, 12]);
      ctx.strokeStyle = '#64748B';
      ctx.beginPath();
      ctx.moveTo(w * 0.5, h * 0.4);
      ctx.lineTo(w * 0.5, h);
      ctx.stroke();
      ctx.setLineDash([]);

      drawOverlay(w, h);
    };

    // Set initial canvas size immediately
    canvas.width = 800;
    canvas.height = 450;
    drawFallbackBackdrop(800, 450);

    const img = new Image();
    img.src = imageSrc || 'https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80';

    img.onload = () => {
      canvas.width = img.naturalWidth || 800;
      canvas.height = img.naturalHeight || 450;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      drawOverlay(canvas.width, canvas.height);
    };

    img.onerror = () => {
      drawFallbackBackdrop(800, 450);
    };
  }, [imageSrc, vehicles, hasAccident, severity, confidenceScore]);

  return (
    <div className={`relative w-full h-full overflow-hidden rounded-xl bg-gray-950 ${className}`}>
      <canvas ref={canvasRef} className="w-full h-full object-contain" />
    </div>
  );
};
