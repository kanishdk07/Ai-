import React from 'react';
import { useAuth } from '../context/AuthContext';
import { SystemSettingsForm } from '../components/admin/SystemSettingsForm';
import { MaintenanceControl } from '../components/admin/MaintenanceControl';
import { SystemHealthCard } from '../components/admin/SystemHealthCard';
import { AuditLogViewer } from '../components/admin/AuditLogViewer';
import { NotificationSettingsPanel } from '../components/admin/NotificationSettingsPanel';
import { Sliders, ShieldAlert, Lock } from 'lucide-react';

export const AdminSettingsPage: React.FC = () => {
  const { isAdmin } = useAuth();

  if (!isAdmin) {
    return (
      <div className="p-12 text-center text-gray-400 bg-gray-900/60 border border-gray-800 rounded-2xl space-y-4">
        <Lock className="w-12 h-12 text-red-500 mx-auto" />
        <h2 className="text-lg font-bold text-white">Access Restricted (Admin Only)</h2>
        <p className="text-xs text-gray-400 max-w-sm mx-auto">
          Administrative controls, maintenance mode toggles, and system rule configurations require Chief Control Officer (Admin) privileges.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gray-900/80 border border-gray-800 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-red-500" />
            <h1 className="text-xl font-extrabold text-white tracking-wide">
              Administrator Controls & System Configuration
            </h1>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            System health telemetry, repeat interval rules, maintenance mode, and audit logging
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <SystemHealthCard />
        <MaintenanceControl />
        <NotificationSettingsPanel />
        <SystemSettingsForm />
        <AuditLogViewer />
      </div>
    </div>
  );
};
