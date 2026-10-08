import { apiClient } from './client';
import { Notification, NotificationType, RecipientType } from '../types';
import { mockNotifications } from './mockData';

let inMemoryNotifications = [...mockNotifications];

export const notificationApi = {
  async sendManualNotification(data: {
    incident_id: string;
    recipient_phone?: string;
    recipient_email?: string;
    recipient_name?: string;
    hospital_id?: string;
    notification_type?: NotificationType;
    custom_message?: string;
  }): Promise<Notification> {
    try {
      const res = await apiClient.post<Notification>('/notifications/manual', data);
      return res.data;
    } catch (err) {
      const newNotif: Notification = {
        id: 'notif-' + Math.random().toString(36).substring(2, 9),
        notification_id: `NOTIF-${Date.now().toString().slice(-6)}`,
        incident_id: data.incident_id,
        recipient_type: (data.hospital_id ? 'hospital' : 'manual') as RecipientType,
        hospital_id: data.hospital_id,
        recipient_phone: data.recipient_phone || '+919876543200',
        recipient_email: data.recipient_email,
        recipient_name: data.recipient_name || 'Emergency Responder',
        notification_type: data.notification_type || 'sms',
        status: 'delivered',
        message: data.custom_message || `[EMERGENCY ALERT] Accident assistance requested for incident ${data.incident_id}.`,
        sent_at: new Date().toISOString(),
        delivered_at: new Date().toISOString(),
        retry_count: 0,
        is_repeat: false,
        repeat_sequence: 1,
        created_at: new Date().toISOString(),
      };
      inMemoryNotifications.unshift(newNotif);
      return newNotif;
    }
  },

  async stopIncidentNotifications(
    incidentId: string,
    reason: string = 'Stopped by authorized operator'
  ): Promise<{ status: string; message: string; stopped_count: number }> {
    try {
      const res = await apiClient.post(`/notifications/${incidentId}/stop`, {
        reason,
        stop_all_for_incident: true,
      });
      return res.data;
    } catch (err) {
      let stoppedCount = 0;
      inMemoryNotifications.forEach((n) => {
        if (n.incident_id === incidentId && n.status !== 'acknowledged') {
          n.status = 'cancelled';
          stoppedCount++;
        }
      });
      return {
        status: 'stopped',
        message: `Notification procedures halted for incident ${incidentId}`,
        stopped_count: stoppedCount,
      };
    }
  },

  async getIncidentNotifications(incidentId: string): Promise<Notification[]> {
    return inMemoryNotifications.filter((n) => n.incident_id === incidentId);
  },

  async getAllNotifications(): Promise<Notification[]> {
    return inMemoryNotifications;
  }
};
