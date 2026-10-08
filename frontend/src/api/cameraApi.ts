import { apiClient } from './client';
import { Camera, CameraType, CameraStatus } from '../types';
import { mockCameras } from './mockData';

let inMemoryCameras = [...mockCameras];

export const cameraApi = {
  async getCameras(params?: { camera_type?: CameraType; status?: CameraStatus; skip?: number; limit?: number }): Promise<{ cameras: Camera[]; total: number }> {
    try {
      const res = await apiClient.get<{ cameras: Camera[]; total: number }>('/cameras', { params });
      return res.data;
    } catch (err) {
      let filtered = [...inMemoryCameras];
      if (params?.camera_type) {
        filtered = filtered.filter((c) => c.camera_type === params.camera_type);
      }
      if (params?.status) {
        filtered = filtered.filter((c) => c.status === params.status);
      }
      return { cameras: filtered, total: filtered.length };
    }
  },

  async getCameraById(id: string): Promise<Camera> {
    try {
      const res = await apiClient.get<Camera>(`/cameras/${id}`);
      return res.data;
    } catch (err) {
      const found = inMemoryCameras.find((c) => c.id === id || c.camera_id === id);
      if (!found) throw new Error('Camera not found');
      return found;
    }
  },

  async createCamera(data: Partial<Camera>): Promise<Camera> {
    try {
      const res = await apiClient.post<Camera>('/cameras', data);
      return res.data;
    } catch (err) {
      const newCam: Camera = {
        id: 'cam-' + Math.random().toString(36).substring(2, 9),
        camera_id: data.camera_id || `CAM-${Date.now().toString().slice(-4)}`,
        name: data.name || 'New Highway Camera',
        camera_type: data.camera_type || 'ip_cctv',
        location_name: data.location_name || 'Highway Section',
        latitude: data.latitude || 28.6139,
        longitude: data.longitude || 77.2090,
        description: data.description || '',
        status: 'online',
        is_monitoring: true,
        health_score: 100,
        total_detections: 0,
        uptime_percentage: 100,
        created_at: new Date().toISOString(),
        connection_config: data.connection_config,
      };
      inMemoryCameras.unshift(newCam);
      return newCam;
    }
  },

  async updateCamera(id: string, data: Partial<Camera>): Promise<Camera> {
    try {
      const res = await apiClient.patch<Camera>(`/cameras/${id}`, data);
      return res.data;
    } catch (err) {
      const idx = inMemoryCameras.findIndex((c) => c.id === id || c.camera_id === id);
      if (idx === -1) throw new Error('Camera not found');
      inMemoryCameras[idx] = { ...inMemoryCameras[idx], ...data, updated_at: new Date().toISOString() };
      return inMemoryCameras[idx];
    }
  },

  async startMonitoring(id: string): Promise<Camera> {
    try {
      const res = await apiClient.post<Camera>(`/cameras/${id}/start`);
      return res.data;
    } catch (err) {
      const idx = inMemoryCameras.findIndex((c) => c.id === id || c.camera_id === id);
      if (idx !== -1) {
        inMemoryCameras[idx] = {
          ...inMemoryCameras[idx],
          is_monitoring: true,
          status: 'monitoring',
          last_active_at: new Date().toISOString(),
        };
        return inMemoryCameras[idx];
      }
      throw new Error('Camera not found');
    }
  },

  async stopMonitoring(id: string): Promise<Camera> {
    try {
      const res = await apiClient.post<Camera>(`/cameras/${id}/stop`);
      return res.data;
    } catch (err) {
      const idx = inMemoryCameras.findIndex((c) => c.id === id || c.camera_id === id);
      if (idx !== -1) {
        inMemoryCameras[idx] = {
          ...inMemoryCameras[idx],
          is_monitoring: false,
          status: 'online',
        };
        return inMemoryCameras[idx];
      }
      throw new Error('Camera not found');
    }
  },

  async deleteCamera(id: string): Promise<void> {
    try {
      await apiClient.delete(`/cameras/${id}`);
    } catch (err) {
      inMemoryCameras = inMemoryCameras.filter((c) => c.id !== id && c.camera_id !== id);
    }
  }
};
