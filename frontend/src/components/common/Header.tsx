import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useSettings } from '../../context/SettingsContext';
import { useWebSocket } from '../../context/WebSocketContext';
import { useIncidents } from '../../context/IncidentContext';
import { EmergencyStopModal } from './EmergencyStopModal';
import {
  ShieldAlert,
  Radio,
  Volume2,
  VolumeX,
  Sun,
  Moon,
  AlertOctagon,
  Wrench,
  LogOut,
  User as UserIcon,
  ChevronDown,
  Sparkles,
} from 'lucide-react';
import { UserRole } from '../../types';

interface HeaderProps {
  onOpenDemoGenerator?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenDemoGenerator }) => {
  const { user, role, logout, switchRole, isAdmin } = useAuth();
  const { settings, theme, toggleTheme, audioAlertsEnabled, toggleAudioAlerts } = useSettings();
  const { connectionState, reconnect } = useWebSocket();
  const { highSeverityCount } = useIncidents();

  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState<boolean>(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState<boolean>(false);

  return (
    <>
      <header className="h-16 bg-gray-900/90 backdrop-blur-md border-b border-gray-800 px-4 md:px-6 flex items-center justify-between sticky top-0 z-40">
        {/* Brand & System Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 via-red-500 to-amber-500 flex items-center justify-center text-white shadow-lg shadow-red-600/30">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base md:text-lg tracking-wider text-white font-['Outfit']">
                  SAFEWAY<span className="text-red-500">.AI</span>
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-red-950 text-red-400 border border-red-800/60">
                  Highway Emergency Net
                </span>
              </div>
              <p className="text-[11px] text-gray-400 font-mono hidden md:block">
                AI Accident Detection & Hospital Dispatch
              </p>
            </div>
          </div>

          {/* WebSocket Connection Pill */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-gray-800/80 border border-gray-700/60 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                connectionState === 'connected'
                  ? 'bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse'
                  : connectionState === 'connecting' || connectionState === 'reconnecting'
                  ? 'bg-amber-400 animate-ping'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-gray-300 font-mono capitalize">
              {connectionState === 'connected' ? 'Live WS Link' : connectionState}
            </span>
            {connectionState === 'disconnected' && (
              <button
                onClick={reconnect}
                className="text-[10px] text-red-400 underline hover:text-red-300"
              >
                Reconnect
              </button>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 md:gap-3">
          {/* Demo AI Event Generator button for testing */}
          {onOpenDemoGenerator && (
            <button
              onClick={onOpenDemoGenerator}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold tracking-wide shadow-md shadow-purple-600/20 transition"
              title="Trigger simulated AI accident detection for testing"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Simulate AI Detection</span>
            </button>
          )}

          {/* Maintenance Mode Indicator */}
          {settings.maintenance_mode && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/20 border border-amber-500/50 rounded-lg text-amber-400 text-xs font-bold animate-pulse">
              <Wrench className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">MAINTENANCE</span>
            </div>
          )}

          {/* High Severity Pulse Badge */}
          {highSeverityCount > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-red-950 border border-red-500 rounded-lg text-red-400 text-xs font-bold animate-radar">
              <Radio className="w-3.5 h-3.5" />
              <span>{highSeverityCount} Critical</span>
            </div>
          )}

          {/* Audio Chime Toggle */}
          <button
            onClick={toggleAudioAlerts}
            className={`p-2 rounded-xl border transition ${
              audioAlertsEnabled
                ? 'bg-gray-800 border-gray-700 text-gray-200 hover:text-white hover:bg-gray-700'
                : 'bg-red-950/40 border-red-800/40 text-red-400 hover:bg-red-900/40'
            }`}
            title={audioAlertsEnabled ? 'Emergency Chimes Active (Click to Mute)' : 'Audio Muted (Click to Unmute)'}
          >
            {audioAlertsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl text-gray-200 hover:text-white transition"
            title="Toggle Light/Dark Theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-400" />}
          </button>

          {/* Critical Emergency Stop Button */}
          <button
            onClick={() => setIsEmergencyModalOpen(true)}
            className="flex items-center gap-1.5 px-3 md:px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs md:text-sm font-extrabold tracking-wider shadow-lg shadow-red-600/40 hover:scale-105 active:scale-95 transition"
          >
            <AlertOctagon className="w-4 h-4" />
            <span>STOP</span>
          </button>

          {/* User Role Menu */}
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 pl-2 pr-3 py-1.5 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-xl text-sm transition"
            >
              <div className="w-7 h-7 rounded-lg bg-gray-700 flex items-center justify-center text-gray-300">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-xs font-semibold text-white leading-none">{user?.username || 'User'}</p>
                <p className="text-[10px] text-red-400 uppercase font-bold tracking-wider leading-none mt-1">
                  {role}
                </p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-gray-900 border border-gray-750 rounded-2xl shadow-2xl py-2 z-50 animate-fadeIn">
                <div className="px-4 py-2 border-b border-gray-800">
                  <p className="text-xs text-gray-400">Authenticated As</p>
                  <p className="text-sm font-bold text-white">{user?.full_name || user?.username}</p>
                  <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                </div>

                <div className="px-3 py-2 border-b border-gray-800">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5">
                    Quick Role Switcher (Testing)
                  </p>
                  <div className="grid grid-cols-3 gap-1">
                    {(['admin', 'operator', 'viewer'] as UserRole[]).map((r) => (
                      <button
                        key={r}
                        onClick={() => {
                          switchRole(r);
                          setIsUserMenuOpen(false);
                        }}
                        className={`px-2 py-1 rounded-md text-[11px] font-bold uppercase transition ${
                          role === r
                            ? 'bg-red-600 text-white'
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={() => {
                    logout();
                    setIsUserMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-400 hover:bg-gray-800 transition text-left"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out Session
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Emergency Stop Modal */}
      <EmergencyStopModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
      />
    </>
  );
};
