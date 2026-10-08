import React, { createContext, useContext, useState, useEffect } from 'react';
import { SystemSettings, SystemHealth } from '../types';
import { adminApi } from '../api/adminApi';
import { mockSystemSettings, mockSystemHealth } from '../api/mockData';

interface SettingsContextType {
  settings: SystemSettings;
  health: SystemHealth;
  theme: 'dark' | 'light';
  audioAlertsEnabled: boolean;
  isLoading: boolean;
  toggleTheme: () => void;
  toggleAudioAlerts: () => void;
  updateSettings: (newSettings: Partial<SystemSettings>) => Promise<void>;
  setMaintenanceMode: (enabled: boolean, reason?: string) => Promise<void>;
  emergencyStopAll: (reason?: string) => Promise<{ stopped_count: number; message: string }>;
  refreshHealth: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<SystemSettings>(mockSystemSettings);
  const [health, setHealth] = useState<SystemHealth>(mockSystemHealth);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [audioAlertsEnabled, setAudioAlertsEnabled] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    // Load theme
    const savedTheme = localStorage.getItem('safeway_theme') as 'dark' | 'light' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.classList.toggle('dark', savedTheme === 'dark');
    } else {
      document.documentElement.classList.add('dark');
    }

    // Load audio preference
    const savedAudio = localStorage.getItem('safeway_audio');
    if (savedAudio !== null) {
      setAudioAlertsEnabled(savedAudio === 'true');
    }

    // Fetch initial settings and health
    const fetchData = async () => {
      try {
        const [sett, hlth] = await Promise.all([
          adminApi.getSystemSettings(),
          adminApi.getSystemHealth(),
        ]);
        setSettings(sett);
        setHealth(hlth);
      } catch {
        // Mock fallback
      }
    };

    fetchData();

    // Health check polling every 20 seconds
    const interval = setInterval(async () => {
      try {
        const hlth = await adminApi.getSystemHealth();
        setHealth(hlth);
      } catch {}
    }, 20000);

    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('safeway_theme', next);
    document.documentElement.classList.toggle('dark', next === 'dark');
  };

  const toggleAudioAlerts = () => {
    const next = !audioAlertsEnabled;
    setAudioAlertsEnabled(next);
    localStorage.setItem('safeway_audio', String(next));
  };

  const updateSettings = async (newSettings: Partial<SystemSettings>) => {
    setIsLoading(true);
    try {
      const updated = await adminApi.updateSystemSettings(newSettings);
      setSettings(updated);
    } finally {
      setIsLoading(false);
    }
  };

  const setMaintenanceMode = async (enabled: boolean, reason?: string) => {
    setIsLoading(true);
    try {
      await adminApi.setMaintenanceMode(enabled, reason);
      setSettings((prev) => ({ ...prev, maintenance_mode: enabled }));
      setHealth((prev) => ({ ...prev, maintenance_mode: enabled }));
    } finally {
      setIsLoading(false);
    }
  };

  const emergencyStopAll = async (reason?: string) => {
    setIsLoading(true);
    try {
      const res = await adminApi.stopAllNotifications(reason);
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const refreshHealth = async () => {
    const hlth = await adminApi.getSystemHealth();
    setHealth(hlth);
  };

  return (
    <SettingsContext.Provider
      value={{
        settings,
        health,
        theme,
        audioAlertsEnabled,
        isLoading,
        toggleTheme,
        toggleAudioAlerts,
        updateSettings,
        setMaintenanceMode,
        emergencyStopAll,
        refreshHealth,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) throw new Error('useSettings must be used within a SettingsProvider');
  return context;
};
