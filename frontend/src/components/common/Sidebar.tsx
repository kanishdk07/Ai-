import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useIncidents } from '../../context/IncidentContext';
import { useCameras } from '../../context/CameraContext';
import {
  LayoutDashboard,
  Video,
  Cctv,
  AlertTriangle,
  MapPin,
  Building2,
  BellRing,
  Sliders,
  Radio,
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'monitoring'
  | 'cameras'
  | 'incidents'
  | 'map'
  | 'hospitals'
  | 'notifications'
  | 'admin';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate }) => {
  const { isAdmin, isOperator } = useAuth();
  const { unacknowledgedCount } = useIncidents();
  const { monitoringCount } = useCameras();

  const navItems: { id: PageId; label: string; icon: React.FC<{ className?: string }>; badge?: number | string; badgeColor?: string; adminOnly?: boolean; operatorOnly?: boolean }[] = [
    {
      id: 'dashboard',
      label: 'Main Dashboard',
      icon: LayoutDashboard,
    },
    {
      id: 'monitoring',
      label: 'Live AI Monitoring',
      icon: Video,
      badge: `${monitoringCount} Live`,
      badgeColor: 'bg-emerald-950 text-emerald-400 border-emerald-800/60',
    },
    {
      id: 'cameras',
      label: 'Camera Management',
      icon: Cctv,
    },
    {
      id: 'incidents',
      label: 'Accident Incidents',
      icon: AlertTriangle,
      badge: unacknowledgedCount > 0 ? unacknowledgedCount : undefined,
      badgeColor: 'bg-red-950 text-red-400 border-red-800 animate-pulse',
    },
    {
      id: 'map',
      label: 'Interactive Map',
      icon: MapPin,
    },
    {
      id: 'hospitals',
      label: 'Hospital Directory',
      icon: Building2,
    },
    {
      id: 'notifications',
      label: 'Emergency Alerts',
      icon: BellRing,
    },
    {
      id: 'admin',
      label: 'Admin & Settings',
      icon: Sliders,
      adminOnly: true,
    },
  ];

  return (
    <aside className="w-64 bg-gray-900/95 border-r border-gray-800 flex flex-col justify-between py-5 shrink-0 hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="space-y-6 px-3">
        <div>
          <p className="px-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2 font-mono">
            Emergency Operations
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              if (item.adminOnly && !isAdmin) return null;

              const Icon = item.icon;
              const isActive = activePage === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition group ${
                    isActive
                      ? 'bg-red-600 text-white shadow-lg shadow-red-600/30'
                      : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800/70'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`w-4 h-4 transition ${
                        isActive ? 'text-white' : 'text-gray-400 group-hover:text-red-400'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={`px-2 py-0.5 text-[11px] font-bold rounded-full border ${
                        isActive
                          ? 'bg-white/20 text-white border-white/30'
                          : item.badgeColor || 'bg-gray-800 text-gray-300 border-gray-700'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Live Highway Telemetry Box */}
        <div className="mx-2 p-3.5 bg-gray-950/80 rounded-xl border border-gray-800 text-xs space-y-2">
          <div className="flex items-center justify-between text-gray-400">
            <span className="flex items-center gap-1.5 font-mono text-[11px]">
              <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
              AI Core Model
            </span>
            <span className="text-emerald-400 font-bold">YOLO-v9</span>
          </div>
          <div className="flex items-center justify-between text-gray-400">
            <span className="font-mono text-[11px]">Inference Rate</span>
            <span className="text-gray-200 font-bold">30 FPS / 135ms</span>
          </div>
          <div className="flex items-center justify-between text-gray-400">
            <span className="font-mono text-[11px]">Auto Dispatch</span>
            <span className="text-emerald-400 font-bold">ENABLED</span>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="px-5 text-[11px] text-gray-400 border-t border-gray-800/80 pt-4">
        <p className="font-semibold text-gray-300">Highway Authority Command</p>
        <p className="font-mono text-[10px] mt-0.5">Version 1.0.0 (Prod Release)</p>
      </div>
    </aside>
  );
};
