/// <reference types="vite/client" />
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to attach JWT
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('safeway_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('safeway_refresh_token');

      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          if (res.data?.access_token) {
            localStorage.setItem('safeway_access_token', res.data.access_token);
            if (res.data.refresh_token) {
              localStorage.setItem('safeway_refresh_token', res.data.refresh_token);
            }
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
            }
            return apiClient(originalRequest);
          }
        } catch (refreshErr) {
          localStorage.removeItem('safeway_access_token');
          localStorage.removeItem('safeway_refresh_token');
          localStorage.removeItem('safeway_user');
          window.dispatchEvent(new CustomEvent('auth:expired'));
        }
      }
    }

    return Promise.reject(error);
  }
);
