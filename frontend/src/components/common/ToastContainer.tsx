import React from 'react';
import { useIncidents } from '../../context/IncidentContext';
import { AlertTriangle, CheckCircle2, Info, X, ExternalLink, Bell } from 'lucide-react';

interface ToastContainerProps {
  onSelectIncident?: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ onSelectIncident }) => {
  const { toasts, removeToast, selectIncidentById } = useIncidents();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-md w-full pointer-events-none">
      {toasts.map((toast) => {
        const isIncident = toast.type === 'incident';
        const isSuccess = toast.type === 'success';
        const isWarning = toast.type === 'warning';

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 p-4 rounded-2xl shadow-2xl backdrop-blur-xl border transition-all duration-300 transform translate-y-0 ${
              isIncident
                ? 'bg-gray-900/95 border-red-500 shadow-red-900/40 text-red-200 animate-radar'
                : isSuccess
                ? 'bg-gray-900/95 border-emerald-500/80 shadow-emerald-950/40 text-emerald-200'
                : isWarning
                ? 'bg-gray-900/95 border-amber-500/80 shadow-amber-950/40 text-amber-200'
                : 'bg-gray-900/95 border-blue-500/80 shadow-blue-950/40 text-blue-200'
            }`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {isIncident ? (
                <div className="p-2 bg-red-600 rounded-xl text-white animate-bounce">
                  <AlertTriangle className="w-5 h-5" />
                </div>
              ) : isSuccess ? (
                <div className="p-2 bg-emerald-600/20 rounded-xl text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              ) : isWarning ? (
                <div className="p-2 bg-amber-600/20 rounded-xl text-amber-400">
                  <Bell className="w-5 h-5" />
                </div>
              ) : (
                <div className="p-2 bg-blue-600/20 rounded-xl text-blue-400">
                  <Info className="w-5 h-5" />
                </div>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h4 className="text-sm font-bold text-white tracking-wide truncate">{toast.title}</h4>
                <span className="text-[10px] text-gray-400 font-mono flex-shrink-0">{toast.timestamp}</span>
              </div>
              <p className="text-xs text-gray-300 mt-1 leading-relaxed line-clamp-2">{toast.message}</p>

              {toast.incidentId && (
                <button
                  onClick={() => {
                    selectIncidentById(toast.incidentId!);
                    if (onSelectIncident) onSelectIncident(toast.incidentId!);
                    removeToast(toast.id);
                  }}
                  className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-bold transition shadow-sm"
                >
                  <ExternalLink className="w-3 h-3" />
                  Inspect Incident
                </button>
              )}
            </div>

            <button
              onClick={() => removeToast(toast.id)}
              className="flex-shrink-0 p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
