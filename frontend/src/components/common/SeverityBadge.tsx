import React from 'react';
import { SeverityLevel } from '../../types';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface SeverityBadgeProps {
  severity: SeverityLevel;
  showIcon?: boolean;
  pulse?: boolean;
  className?: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  showIcon = true,
  pulse = true,
  className = '',
}) => {
  switch (severity) {
    case 'high':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-red-950/80 text-red-400 border border-red-500/40 ${
            pulse ? 'animate-pulse' : ''
          } ${className}`}
        >
          {showIcon && <AlertTriangle className="w-3.5 h-3.5 text-red-400" />}
          High Severity
        </span>
      );
    case 'medium':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-950/80 text-amber-400 border border-amber-500/40 ${className}`}
        >
          {showIcon && <AlertCircle className="w-3.5 h-3.5 text-amber-400" />}
          Medium Severity
        </span>
      );
    case 'low':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-blue-950/80 text-blue-400 border border-blue-500/40 ${className}`}
        >
          {showIcon && <Info className="w-3.5 h-3.5 text-blue-400" />}
          Low Severity
        </span>
      );
    default:
      return null;
  }
};
