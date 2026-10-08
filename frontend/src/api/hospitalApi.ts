import { apiClient } from './client';
import { Hospital, NearbyHospital } from '../types';
import { mockHospitals } from './mockData';

let inMemoryHospitals = [...mockHospitals];

function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 10) / 10;
}

export const hospitalApi = {
  async getHospitals(params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<{ hospitals: Hospital[]; total: number }> {
    try {
      const res = await apiClient.get<{ hospitals: Hospital[]; total: number }>('/hospitals', { params });
      return res.data;
    } catch (err) {
      let filtered = [...inMemoryHospitals];
      if (params?.is_active !== undefined) {
        filtered = filtered.filter((h) => h.is_active === params.is_active);
      }
      return { hospitals: filtered, total: filtered.length };
    }
  },

  async getNearbyHospitals(params: {
    latitude: number;
    longitude: number;
    radius_km?: number;
    limit?: number;
  }): Promise<NearbyHospital[]> {
    try {
      const res = await apiClient.get<NearbyHospital[]>('/hospitals/nearby', { params });
      return res.data;
    } catch (err) {
      const radius = params.radius_km || 50;
      const nearby: NearbyHospital[] = inMemoryHospitals
        .map((h) => ({
          ...h,
          distance_km: calculateDistance(params.latitude, params.longitude, h.latitude, h.longitude),
        }))
        .filter((h) => h.distance_km <= radius)
        .sort((a, b) => a.distance_km - b.distance_km)
        .slice(0, params.limit || 5);

      return nearby;
    }
  },

  async getHospitalById(id: string): Promise<Hospital> {
    try {
      const res = await apiClient.get<Hospital>(`/hospitals/${id}`);
      return res.data;
    } catch (err) {
      const found = inMemoryHospitals.find((h) => h.id === id);
      if (!found) throw new Error('Hospital not found');
      return found;
    }
  },

  async createHospital(data: Partial<Hospital>): Promise<Hospital> {
    try {
      const res = await apiClient.post<Hospital>('/hospitals', data);
      return res.data;
    } catch (err) {
      const newHosp: Hospital = {
        id: 'hosp-' + Math.random().toString(36).substring(2, 9),
        name: data.name || 'New Emergency Hospital',
        phone_numbers: data.phone_numbers || ['+919876543200'],
        email: data.email || 'emergency@hospital.org',
        address: data.address || 'Highway Road',
        latitude: data.latitude || 28.6139,
        longitude: data.longitude || 77.2090,
        has_emergency_dept: data.has_emergency_dept ?? true,
        has_trauma_center: data.has_trauma_center ?? false,
        has_ambulance: data.has_ambulance ?? true,
        is_available: true,
        is_24_7: data.is_24_7 ?? true,
        accepts_sms: data.accepts_sms ?? true,
        accepts_email: data.accepts_email ?? true,
        accepts_call: data.accepts_call ?? true,
        total_responses: 0,
        successful_responses: 0,
        is_active: true,
        is_verified: true,
        created_at: new Date().toISOString(),
      };
      inMemoryHospitals.unshift(newHosp);
      return newHosp;
    }
  },

  async updateHospital(id: string, data: Partial<Hospital>): Promise<Hospital> {
    try {
      const res = await apiClient.patch<Hospital>(`/hospitals/${id}`, data);
      return res.data;
    } catch (err) {
      const idx = inMemoryHospitals.findIndex((h) => h.id === id);
      if (idx === -1) throw new Error('Hospital not found');
      inMemoryHospitals[idx] = { ...inMemoryHospitals[idx], ...data };
      return inMemoryHospitals[idx];
    }
  },

  async toggleHospitalStatus(id: string, is_active: boolean): Promise<Hospital> {
    return this.updateHospital(id, { is_active });
  }
};
