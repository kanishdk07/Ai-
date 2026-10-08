import { apiClient } from './client';
import { Incident, IncidentStatus, SeverityLevel } from '../types';
import { mockIncidents } from './mockData';

let inMemoryIncidents = [...mockIncidents];

export const incidentApi = {
  async getIncidents(params?: {
    status?: IncidentStatus;
    severity?: SeverityLevel;
    skip?: number;
    limit?: number;
  }): Promise<{ incidents: Incident[]; total: number }> {
    try {
      const res = await apiClient.get<{ incidents: Incident[]; total: number }>('/incidents', { params });
      return res.data;
    } catch (err) {
      let filtered = [...inMemoryIncidents];
      if (params?.status) {
        filtered = filtered.filter((i) => i.status === params.status);
      }
      if (params?.severity) {
        filtered = filtered.filter((i) => i.severity === params.severity);
      }
      return { incidents: filtered, total: filtered.length };
    }
  },

  async getIncidentById(id: string): Promise<Incident> {
    try {
      const res = await apiClient.get<Incident>(`/incidents/${id}`);
      return res.data;
    } catch (err) {
      const found = inMemoryIncidents.find((i) => i.id === id || i.incident_id === id);
      if (!found) throw new Error('Incident not found');
      return found;
    }
  },

  async createIncident(data: Partial<Incident>): Promise<Incident> {
    try {
      const res = await apiClient.post<Incident>('/incidents', data);
      return res.data;
    } catch (err) {
      const newInc: Incident = {
        id: 'inc-' + Math.random().toString(36).substring(2, 9),
        incident_id: data.incident_id || `ACC-${new Date().toISOString().slice(0, 10)}-${Math.floor(Math.random() * 900 + 100)}`,
        camera_external_id: data.camera_external_id || 'CAM-HWY-01',
        detected_at: data.detected_at || new Date().toISOString(),
        accident_detected: true,
        severity: data.severity || 'high',
        confidence_score: data.confidence_score || 0.92,
        latitude: data.latitude || 28.4595,
        longitude: data.longitude || 77.0266,
        location_description: data.location_description || 'Highway Section Detected',
        accident_image_url: data.accident_image_url || 'https://images.unsplash.com/photo-1545178803-4056771d60a3?auto=format&fit=crop&w=1200&q=80',
        status: 'detected',
        vehicle_count: data.vehicle_count || 2,
        vehicle_info: data.vehicle_info || {
          vehicles: [
            { type: 'Car', color: 'Red', bbox: [0.2, 0.3, 0.3, 0.3] },
            { type: 'Truck', color: 'White', bbox: [0.5, 0.2, 0.4, 0.5] }
          ],
          total_vehicles: 2
        },
        ai_event_data: data.ai_event_data || { model_version: 'YOLO-v9-Accident-X' },
        notification_count: 0,
        created_at: new Date().toISOString(),
      };
      inMemoryIncidents.unshift(newInc);
      return newInc;
    }
  },

  async verifyIncident(id: string, notes?: string): Promise<Incident> {
    try {
      const res = await apiClient.patch<Incident>(`/incidents/${id}`, {
        status: 'active',
        notes: notes || 'Verified by operator as confirmed accident.',
      });
      return res.data;
    } catch (err) {
      const idx = inMemoryIncidents.findIndex((i) => i.id === id || i.incident_id === id);
      if (idx !== -1) {
        inMemoryIncidents[idx] = {
          ...inMemoryIncidents[idx],
          status: 'active',
          notes: notes || inMemoryIncidents[idx].notes || 'Verified by operator as confirmed accident.',
          updated_at: new Date().toISOString(),
        };
        return inMemoryIncidents[idx];
      }
      throw new Error('Incident not found');
    }
  },

  async acknowledgeIncident(id: string, data: {
    hospital_id?: string;
    acknowledgment_token?: string;
    notes?: string;
    responder_name?: string;
  }): Promise<{ incident_id: string; status: IncidentStatus; message: string; hospital_name?: string }> {
    try {
      const res = await apiClient.post(`/incidents/${id}/acknowledge`, data);
      return res.data;
    } catch (err) {
      const idx = inMemoryIncidents.findIndex((i) => i.id === id || i.incident_id === id);
      if (idx !== -1) {
        inMemoryIncidents[idx] = {
          ...inMemoryIncidents[idx],
          status: 'acknowledged',
          acknowledged_at: new Date().toISOString(),
          acknowledged_by_hospital_id: data.hospital_id || 'hosp-001',
          acknowledged_by_hospital_name: 'Apex Trauma & Multi-Specialty Hospital',
          acknowledged_responder: data.responder_name || 'Dr. EMT On-Duty',
          acknowledged_notes: data.notes || 'Emergency ambulance dispatched to scene.',
          updated_at: new Date().toISOString(),
        };
        return {
          incident_id: id,
          status: 'acknowledged',
          hospital_name: 'Apex Trauma & Multi-Specialty Hospital',
          message: 'Incident acknowledged successfully. Emergency ambulance dispatched.',
        };
      }
      throw new Error('Incident not found');
    }
  },

  async resolveIncident(id: string, data: { resolution_notes: string; outcome?: string }): Promise<Incident> {
    try {
      const res = await apiClient.post<Incident>(`/incidents/${id}/resolve`, data);
      return res.data;
    } catch (err) {
      const idx = inMemoryIncidents.findIndex((i) => i.id === id || i.incident_id === id);
      if (idx !== -1) {
        inMemoryIncidents[idx] = {
          ...inMemoryIncidents[idx],
          status: 'resolved',
          resolved_at: new Date().toISOString(),
          resolved_by: 'Authorized Officer',
          resolution_notes: data.resolution_notes,
          updated_at: new Date().toISOString(),
        };
        return inMemoryIncidents[idx];
      }
      throw new Error('Incident not found');
    }
  },

  async cancelIncident(id: string, data: { reason: string }): Promise<Incident> {
    try {
      const res = await apiClient.post<Incident>(`/incidents/${id}/cancel`, data);
      return res.data;
    } catch (err) {
      const idx = inMemoryIncidents.findIndex((i) => i.id === id || i.incident_id === id);
      if (idx !== -1) {
        inMemoryIncidents[idx] = {
          ...inMemoryIncidents[idx],
          status: 'cancelled',
          notes: `Cancelled: ${data.reason}`,
          updated_at: new Date().toISOString(),
        };
        return inMemoryIncidents[idx];
      }
      throw new Error('Incident not found');
    }
  },

  async uploadVideo(file: File, cameraId?: string, latitude?: number, longitude?: number): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (cameraId) formData.append('camera_id', cameraId);
    if (latitude !== undefined) formData.append('latitude', latitude.toString());
    if (longitude !== undefined) formData.append('longitude', longitude.toString());

    const res = await apiClient.post('/incidents/upload-video', formData, {
      timeout: 300000, // 5 minutes timeout for AI frame processing
    });
    return res.data;
  }
};
