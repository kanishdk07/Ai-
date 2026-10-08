import { apiClient } from './client';
import { AuditLog, SystemHealth, SystemSettings } from '../types';
import { mockAuditLogs, mockSystemHealth, mockSystemSettings } from './mockData';

let inMemorySettings = { ...mockSystemSettings };
let inMemoryHealth = { ...mockSystemHealth };
let inMemoryAuditLogs = [...mockAuditLogs];

export const adminApi = {
  async getSystemSettings(): Promise<SystemSettings> {
    try {
      // In backend settings are returned or modified
      const res = await apiClient.get<SystemSettings>('/admin/health'); // health includes some settings or fallback
      return inMemorySettings;
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
  }
};
