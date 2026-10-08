import React from 'react';
import { IncidentStatus } from '../../types';
import { CheckCircle2, Clock, Bell, CheckCheck, XCircle, Radio } from 'lucide-react';

interface StatusBadgeProps {
  status: IncidentStatus;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  switch (status) {
    case 'detected':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 ${className}`}>
          <Radio className="w-3.5 h-3.5 animate-spin" />
          Unverified AI Detection
        </span>
      );
    case 'active':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/30 ${className}`}>
          <Clock className="w-3.5 h-3.5 animate-pulse" />
          Active Incident
        </span>
      );
    case 'notified':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 ${className}`}>
          <Bell className="w-3.5 h-3.5 animate-bounce" />
          Notified (Awaiting Ack)
        </span>
      );
    case 'acknowledged':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30 ${className}`}>
          <CheckCheck className="w-3.5 h-3.5" />
          Hospital Acknowledged
        </span>
      );
    case 'resolved':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 ${className}`}>
          <CheckCircle2 className="w-3.5 h-3.5" />
          Resolved & Cleared
        </span>
      );
    case 'cancelled':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-700/50 text-slate-400 border border-slate-600/40 ${className}`}>
          <XCircle className="w-3.5 h-3.5" />
          False Alarm (Cancelled)
        </span>
      );
    default:
      return null;
  }
};
