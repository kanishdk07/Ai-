import { apiClient } from './client';
import { TokenResponse, User } from '../types';
import { mockUsers } from './mockData';

export const authApi = {
  async login(username: string, password: string): Promise<{ tokens: TokenResponse; user: User }> {
    try {
      const res = await apiClient.post<TokenResponse>('/auth/login', { username, password });
      const tokens = res.data;
      
      // Get user profile with new token
      localStorage.setItem('safeway_access_token', tokens.access_token);
      localStorage.setItem('safeway_refresh_token', tokens.refresh_token);
      
      const userRes = await apiClient.get<User>('/auth/me');
      return { tokens, user: userRes.data };
    } catch (err) {
      // Offline fallback / Mock simulation
      const foundUser = mockUsers.find(
        (u) => u.username.toLowerCase() === username.toLowerCase()
      ) || mockUsers[0];

      const mockTokens: TokenResponse = {
        access_token: 'mock-jwt-access-token-' + foundUser.role,
        refresh_token: 'mock-jwt-refresh-token-' + foundUser.role,
        token_type: 'bearer',
        expires_in: 1800,
      };

      return { tokens: mockTokens, user: foundUser };
    }
  },

  async getCurrentUser(): Promise<User> {
    try {
      const res = await apiClient.get<User>('/auth/me');
      return res.data;
    } catch (err) {
      const stored = localStorage.getItem('safeway_user');
      if (stored) return JSON.parse(stored);
      return mockUsers[0];
    }
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (err) {
      // ignore
    } finally {
      localStorage.removeItem('safeway_access_token');
      localStorage.removeItem('safeway_refresh_token');
      localStorage.removeItem('safeway_user');
    }
  }
};
