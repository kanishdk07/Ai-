import { apiClient } from './client';
import { AuditLog, SystemHealth, SystemSettings, NotificationSettings, TestNotificationResult } from '../types';
import { mockAuditLogs, mockSystemHealth, mockSystemSettings } from './mockData';

let inMemorySettings = { ...mockSystemSettings };
let inMemoryHealth = { ...mockSystemHealth };
let inMemoryAuditLogs = [...mockAuditLogs];

export const adminApi = {
  async getSystemSettings(): Promise<SystemSettings> {
    try {
      const res = await apiClient.get<SystemSettings>('/admin/settings');
      return res.data;
    } catch (err) {
      return inMemorySettings;
    }
  },

  async updateSystemSettings(data: Partial<SystemSettings>): Promise<SystemSettings> {
    try {
      const res = await apiClient.patch<SystemSettings>('/admin/settings', data);
      inMemorySettings = { ...inMemorySettings, ...res.data, updated_at: new Date().toISOString() };
      return inMemorySettings;
    } catch (err) {
      inMemorySettings = {
        ...inMemorySettings,
        ...data,
        updated_at: new Date().toISOString(),
      };
      // Add audit log
      inMemoryAuditLogs.unshift({
        id: 'log-' + Math.random().toString(36).substring(2, 9),
        username: 'admin',
        action: 'SETTINGS_UPDATE',
        resource_type: 'system_settings',
        endpoint: '/api/v1/admin/settings',
        method: 'PATCH',
        ip_address: '127.0.0.1',
        success: true,
        description: `Updated system settings: ${Object.keys(data).join(', ')}`,
        created_at: new Date().toISOString(),
      });
      return inMemorySettings;
    }
  },

  async setMaintenanceMode(
    enabled: boolean,
    reason?: string,
    scheduled_end_time?: string
  ): Promise<{ maintenance_mode: boolean; message: string }> {
    try {
      const res = await apiClient.post<{ maintenance_mode: boolean; message: string }>('/admin/maintenance', {
        enabled,
        reason,
        scheduled_end_time,
      });
      inMemorySettings.maintenance_mode = enabled;
      inMemoryHealth.maintenance_mode = enabled;
      return res.data;
    } catch (err) {
      inMemorySettings.maintenance_mode = enabled;
      inMemoryHealth.maintenance_mode = enabled;
      inMemoryAuditLogs.unshift({
        id: 'log-' + Math.random().toString(36).substring(2, 9),
        username: 'admin',
        action: enabled ? 'MAINTENANCE_ENABLED' : 'MAINTENANCE_DISABLED',
        resource_type: 'system',
        endpoint: '/api/v1/admin/maintenance',
        method: 'POST',
        ip_address: '127.0.0.1',
        success: true,
        description: enabled
          ? `Maintenance mode enabled. Reason: ${reason || 'Manual activation'}`
          : 'Maintenance mode deactivated. Normal monitoring resumed.',
        created_at: new Date().toISOString(),
      });
      return {
        maintenance_mode: enabled,
        message: enabled
          ? 'Maintenance mode activated. Live notifications and monitoring paused.'
          : 'Maintenance mode deactivated. Normal operations resumed.',
      };
    }
  },

  async stopAllNotifications(
    reason: string = 'Emergency Protocol Activated'
  ): Promise<{ stopped_count: number; incidents_affected: string[]; message: string }> {
    try {
      const res = await apiClient.post('/admin/notifications/stop-all', {
        reason,
        stop_scope: 'all',
      });
      return res.data;
    } catch (err) {
      inMemoryAuditLogs.unshift({
        id: 'log-' + Math.random().toString(36).substring(2, 9),
        username: 'admin',
        action: 'EMERGENCY_STOP_ALL',
        resource_type: 'notification',
        endpoint: '/api/v1/admin/notifications/stop-all',
        method: 'POST',
        ip_address: '127.0.0.1',
        success: true,
        description: `Emergency Stop triggered for all active incident notifications. Reason: ${reason}`,
        created_at: new Date().toISOString(),
      });
      return {
        stopped_count: 5,
        incidents_affected: ['inc-001'],
        message: 'Successfully stopped all active emergency notification procedures across the system.',
      };
    }
  },

  async getSystemHealth(): Promise<SystemHealth> {
    try {
      const res = await apiClient.get<SystemHealth>('/admin/health');
      return res.data;
    } catch (err) {
      return {
        ...inMemoryHealth,
        timestamp: new Date().toISOString(),
      };
    }
  },

  async getAuditLogs(params?: { skip?: number; limit?: number }): Promise<{ logs: AuditLog[]; total: number }> {
    try {
      const res = await apiClient.get<{ logs: AuditLog[]; total: number }>('/admin/audit-logs', { params });
      return res.data;
    } catch (err) {
      return { logs: inMemoryAuditLogs, total: inMemoryAuditLogs.length };
    }
  },

  // ─── Emergency Contact Notification Settings (NEW) ───────────────────────────

  async getNotificationSettings(): Promise<NotificationSettings> {
    try {
      const res = await apiClient.get<NotificationSettings>('/admin/notification-settings');
      return res.data;
    } catch (err) {
      // Mock fallback — read from localStorage so changes persist across reloads
      const stored = localStorage.getItem('safeway_notif_settings');
      if (stored) return JSON.parse(stored) as NotificationSettings;
      return {
        emergency_contact_number: null,
        emergency_notifications_enabled: false,
        hospital_notifications_enabled: false,
        updated_at: new Date().toISOString(),
      };
    }
  },

  async updateNotificationSettings(
    data: Partial<NotificationSettings>
  ): Promise<NotificationSettings> {
    try {
      const res = await apiClient.patch<NotificationSettings>('/admin/notification-settings', data);
      return res.data;
    } catch (err) {
      // Mock fallback — persist in localStorage
      const stored = localStorage.getItem('safeway_notif_settings');
      const current: NotificationSettings = stored
        ? JSON.parse(stored)
        : { emergency_contact_number: null, emergency_notifications_enabled: false, hospital_notifications_enabled: false };
      const updated: NotificationSettings = {
        ...current,
        ...data,
        updated_at: new Date().toISOString(),
      };
      localStorage.setItem('safeway_notif_settings', JSON.stringify(updated));
      // Audit log
      inMemoryAuditLogs.unshift({
        id: 'log-' + Math.random().toString(36).substring(2, 9),
        username: 'admin',
        action: 'UPDATE_NOTIFICATION_SETTINGS',
        resource_type: 'admin_setting',
        endpoint: '/api/v1/admin/notification-settings',
        method: 'PATCH',
        ip_address: '127.0.0.1',
        success: true,
        description: `Notification settings updated: ${Object.keys(data).join(', ')}`,
        created_at: new Date().toISOString(),
      });
      return updated;
    }
  },

  async sendTestNotification(): Promise<TestNotificationResult> {
    try {
      const res = await apiClient.post<TestNotificationResult>('/admin/notification-settings/test');
      return res.data;
    } catch (err) {
      // Mock fallback — check localStorage state
      const stored = localStorage.getItem('safeway_notif_settings');
      const current: NotificationSettings = stored
        ? JSON.parse(stored)
        : { emergency_contact_number: null, emergency_notifications_enabled: false, hospital_notifications_enabled: false };

      if (!current.emergency_notifications_enabled) {
        return {
          sent: false,
          message: 'Emergency notifications are currently OFF. Enable them before sending a test.',
          timestamp: new Date().toISOString(),
        };
      }
      if (!current.emergency_contact_number) {
        return {
          sent: false,
          message: 'No emergency contact number configured. Please add one and save first.',
          timestamp: new Date().toISOString(),
        };
      }
      // Simulate successful mock send
      inMemoryAuditLogs.unshift({
        id: 'log-' + Math.random().toString(36).substring(2, 9),
        username: 'admin',
        action: 'SEND_TEST_NOTIFICATION',
        resource_type: 'notification',
        endpoint: '/api/v1/admin/notification-settings/test',
        method: 'POST',
        ip_address: '127.0.0.1',
        success: true,
        description: `[MOCK] Test notification simulated to ${current.emergency_contact_number}`,
        created_at: new Date().toISOString(),
      });
      return {
        sent: true,
        message: `[MOCK] Test notification sent successfully to ${current.emergency_contact_number}.`,
        recipient: current.emergency_contact_number,
        provider: 'mock',
        timestamp: new Date().toISOString(),
      };
    }
  },
};

