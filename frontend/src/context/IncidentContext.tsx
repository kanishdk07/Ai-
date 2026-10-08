import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Incident, IncidentStatus, SeverityLevel, Notification, WebSocketMessage } from '../types';
import { incidentApi } from '../api/incidentApi';
import { notificationApi } from '../api/notificationApi';
import { useSettings } from './SettingsContext';

interface Toast {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'incident';
  title: string;
  message: string;
  timestamp: string;
  incidentId?: string;
}

interface IncidentContextType {
  incidents: Incident[];
  selectedIncident: Incident | null;
  activeIncidentsCount: number;
  unacknowledgedCount: number;
  resolvedCount: number;
  highSeverityCount: number;
  isLoading: boolean;
  toasts: Toast[];
  filterStatus: string;
  filterSeverity: string;
  searchQuery: string;
  setFilterStatus: (s: string) => void;
  setFilterSeverity: (s: string) => void;
  setSearchQuery: (q: string) => void;
  setSelectedIncident: (inc: Incident | null) => void;
  selectIncidentById: (id: string) => void;
  fetchIncidents: () => Promise<void>;
  createIncident: (data: Partial<Incident>) => Promise<Incident>;
  verifyIncident: (id: string, notes?: string) => Promise<void>;
  acknowledgeIncident: (id: string, hospitalId?: string, responderName?: string, notes?: string) => Promise<void>;
  resolveIncident: (id: string, resolutionNotes: string, outcome?: string) => Promise<void>;
  cancelIncident: (id: string, reason: string) => Promise<void>;
  stopIncidentNotifications: (id: string, reason?: string) => Promise<void>;
  sendManualAlert: (incidentId: string, phone: string, name?: string, customMsg?: string) => Promise<Notification>;
  removeToast: (id: string) => void;
  addToast: (toast: Omit<Toast, 'id' | 'timestamp'>) => void;
}

const IncidentContext = createContext<IncidentContextType | undefined>(undefined);

export const IncidentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { audioAlertsEnabled } = useSettings();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const playAlertSound = useCallback((severity: SeverityLevel) => {
    if (!audioAlertsEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);

      if (severity === 'high') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
        osc.frequency.setValueAtTime(440, audioCtx.currentTime + 0.15); // A4
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      } else {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
      }
    } catch {
      // Audio context might be restricted before user interaction
    }
  }, [audioAlertsEnabled]);

  const addToast = useCallback((toast: Omit<Toast, 'id' | 'timestamp'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: Toast = {
      ...toast,
      id,
      timestamp: new Date().toLocaleTimeString(),
    };
    setToasts((prev) => [newToast, ...prev.slice(0, 5)]); // keep max 6 toasts

    // Auto-dismiss info/success toasts after 6s
    if (toast.type !== 'incident') {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 6000);
    }
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const fetchIncidents = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await incidentApi.getIncidents();
      setIncidents(res.incidents);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  // Listen to WebSocket custom events
  useEffect(() => {
    const handleWsEvent = (e: Event) => {
      const customEvent = e as CustomEvent<WebSocketMessage>;
      const { type, data } = customEvent.detail;

      if (type === 'incident_created') {
        const newIncident: Incident = data;
        setIncidents((prev) => [newIncident, ...prev.filter((i) => i.id !== newIncident.id)]);
        playAlertSound(newIncident.severity);
        addToast({
          type: 'incident',
          title: `🚨 ${newIncident.severity.toUpperCase()} Severity Crash Detected!`,
          message: `${newIncident.location_description || 'Highway Camera'} - AI Confidence ${(newIncident.confidence_score * 100).toFixed(0)}%`,
          incidentId: newIncident.id,
        });
      } else if (type === 'incident_updated') {
        setIncidents((prev) =>
          prev.map((i) => (i.id === data.id || i.incident_id === data.incident_id ? { ...i, ...data } : i))
        );
      } else if (type === 'incident_acknowledged') {
        setIncidents((prev) =>
          prev.map((i) =>
            i.id === data.incident_id || i.incident_id === data.incident_id
              ? { ...i, status: 'acknowledged', acknowledged_by_hospital_name: data.hospital_name, acknowledged_at: data.acknowledged_at }
              : i
          )
        );
        addToast({
          type: 'success',
          title: '🚑 Hospital Acknowledged Incident',
          message: `${data.hospital_name || 'Emergency Team'} is en route to scene.`,
        });
      } else if (type === 'incident_resolved') {
        setIncidents((prev) =>
          prev.map((i) =>
            i.id === data.incident_id || i.incident_id === data.incident_id
              ? { ...i, status: 'resolved', resolved_at: new Date().toISOString() }
              : i
          )
        );
        addToast({
          type: 'info',
          title: '✅ Incident Resolved',
          message: `Incident ${data.incident_id || ''} has been resolved and closed.`,
        });
      } else if (type === 'notification_sent') {
        addToast({
          type: 'info',
          title: '📲 Emergency SMS Dispatched',
          message: `Alert sent to ${data.recipient_phone || 'hospital'} (Cycle #${data.repeat_sequence || 1})`,
        });
      } else if (type === 'notifications_stopped') {
        addToast({
          type: 'warning',
          title: '🛑 Notifications Stopped',
          message: `Notification sequence halted for incident ${data.incident_id || ''}`,
        });
      }
    };

    window.addEventListener('safeway:ws_event', handleWsEvent);
    return () => window.removeEventListener('safeway:ws_event', handleWsEvent);
  }, [playAlertSound, addToast]);

  const selectIncidentById = (id: string) => {
    const found = incidents.find((i) => i.id === id || i.incident_id === id);
    if (found) setSelectedIncident(found);
  };

  const createIncident = async (data: Partial<Incident>) => {
    const created = await incidentApi.createIncident(data);
    setIncidents((prev) => [created, ...prev]);
    playAlertSound(created.severity);
    addToast({
      type: 'incident',
      title: `🚨 Crash Ingested: ${created.incident_id}`,
      message: `${created.location_description || 'Highway'} (${created.severity.toUpperCase()})`,
      incidentId: created.id,
    });
    return created;
  };

  const verifyIncident = async (id: string, notes?: string) => {
    const updated = await incidentApi.verifyIncident(id, notes);
    setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
    if (selectedIncident?.id === id) setSelectedIncident(updated);
    addToast({
      type: 'success',
      title: 'Incident Confirmed',
      message: 'Event verified and emergency workflow initiated.',
    });
  };

  const acknowledgeIncident = async (id: string, hospitalId?: string, responderName?: string, notes?: string) => {
    const res = await incidentApi.acknowledgeIncident(id, {
      hospital_id: hospitalId,
      responder_name: responderName,
      notes,
    });
    setIncidents((prev) =>
      prev.map((i) =>
        i.id === id
          ? {
              ...i,
              status: 'acknowledged',
              acknowledged_by_hospital_name: res.hospital_name,
              acknowledged_responder: responderName,
              acknowledged_notes: notes,
              acknowledged_at: new Date().toISOString(),
            }
          : i
      )
    );
    if (selectedIncident?.id === id) {
      setSelectedIncident((prev) =>
        prev
          ? {
              ...prev,
              status: 'acknowledged',
              acknowledged_by_hospital_name: res.hospital_name,
              acknowledged_responder: responderName,
              acknowledged_notes: notes,
              acknowledged_at: new Date().toISOString(),
            }
          : null
      );
    }
    addToast({
      type: 'success',
      title: 'Hospital Acknowledged',
      message: res.message,
    });
  };

  const resolveIncident = async (id: string, resolutionNotes: string, outcome?: string) => {
    const updated = await incidentApi.resolveIncident(id, { resolution_notes: resolutionNotes, outcome });
    setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
    if (selectedIncident?.id === id) setSelectedIncident(updated);
    addToast({
      type: 'success',
      title: 'Incident Resolved',
      message: 'Highway cleared and incident marked as resolved.',
    });
  };

  const cancelIncident = async (id: string, reason: string) => {
    const updated = await incidentApi.cancelIncident(id, { reason });
    setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
    if (selectedIncident?.id === id) setSelectedIncident(updated);
    addToast({
      type: 'warning',
      title: 'Marked False Positive',
      message: `Incident cancelled: ${reason}`,
    });
  };

  const stopIncidentNotifications = async (id: string, reason?: string) => {
    const res = await notificationApi.stopIncidentNotifications(id, reason);
    setIncidents((prev) =>
      prev.map((i) =>
        i.id === id ? { ...i, notification_stopped_at: new Date().toISOString() } : i
      )
    );
    addToast({
      type: 'warning',
      title: 'Notifications Stopped',
      message: res.message,
    });
  };

  const sendManualAlert = async (incidentId: string, phone: string, name?: string, customMsg?: string) => {
    const notif = await notificationApi.sendManualNotification({
      incident_id: incidentId,
      recipient_phone: phone,
      recipient_name: name,
      custom_message: customMsg,
    });
    setIncidents((prev) =>
      prev.map((i) =>
        i.id === incidentId
          ? {
              ...i,
              status: i.status === 'detected' ? 'notified' : i.status,
              notification_count: (i.notification_count || 0) + 1,
              notification_started_at: i.notification_started_at || new Date().toISOString(),
            }
          : i
      )
    );
    addToast({
      type: 'success',
      title: 'Emergency SMS Sent',
      message: `Alert successfully dispatched to ${phone}`,
    });
    return notif;
  };

  // Metric counts
  const activeIncidentsCount = incidents.filter((i) => ['detected', 'active', 'notified'].includes(i.status)).length;
  const unacknowledgedCount = incidents.filter((i) => ['detected', 'active', 'notified'].includes(i.status)).length;
  const resolvedCount = incidents.filter((i) => i.status === 'resolved').length;
  const highSeverityCount = incidents.filter((i) => i.severity === 'high' && i.status !== 'resolved' && i.status !== 'cancelled').length;

  return (
    <IncidentContext.Provider
      value={{
        incidents,
        selectedIncident,
        activeIncidentsCount,
        unacknowledgedCount,
        resolvedCount,
        highSeverityCount,
        isLoading,
        toasts,
        filterStatus,
        filterSeverity,
        searchQuery,
        setFilterStatus,
        setFilterSeverity,
        setSearchQuery,
        setSelectedIncident,
        selectIncidentById,
        fetchIncidents,
        createIncident,
        verifyIncident,
        acknowledgeIncident,
        resolveIncident,
        cancelIncident,
        stopIncidentNotifications,
        sendManualAlert,
        removeToast,
        addToast,
      }}
    >
      {children}
    </IncidentContext.Provider>
  );
};

export const useIncidents = () => {
  const context = useContext(IncidentContext);
  if (!context) throw new Error('useIncidents must be used within an IncidentProvider');
  return context;
};
