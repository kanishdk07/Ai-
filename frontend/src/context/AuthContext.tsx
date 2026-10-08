import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole, TokenResponse } from '../types';
import { authApi } from '../api/authApi';
import { mockUsers } from '../api/mockData';

interface AuthContextType {
  user: User | null;
  role: UserRole;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  switchRole: (role: UserRole) => void;
  isAdmin: boolean;
  isOperator: boolean;
  isViewer: boolean;
  canManageCameras: boolean;
  canEditSettings: boolean;
  canVerifyIncidents: boolean;
  canTriggerNotifications: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('safeway_access_token');
      const storedUser = localStorage.getItem('safeway_user');

      if (storedToken && storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          // Don't trust mock tokens — clear them and require real login
          if (storedToken.startsWith('mock-')) {
            localStorage.removeItem('safeway_access_token');
            localStorage.removeItem('safeway_user');
            setUser(null);
          } else {
            setUser(parsedUser);
          }
        } catch {
          localStorage.removeItem('safeway_access_token');
          localStorage.removeItem('safeway_user');
          setUser(null);
        }
      } else {
        setUser(null);
      }
      setIsLoading(false);
    };

    initAuth();

    const handleExpired = () => {
      setUser(null);
    };
    window.addEventListener('auth:expired', handleExpired);
    return () => window.removeEventListener('auth:expired', handleExpired);
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const { user: loggedInUser, tokens } = await authApi.login(username, password);
      setUser(loggedInUser);
      localStorage.setItem('safeway_user', JSON.stringify(loggedInUser));
      localStorage.setItem('safeway_access_token', tokens.access_token);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
  };

  const switchRole = (newRole: UserRole) => {
    const target = mockUsers.find((u) => u.role === newRole) || {
      ...mockUsers[0],
      role: newRole,
      username: newRole,
    };
    setUser(target);
    localStorage.setItem('safeway_user', JSON.stringify(target));
    localStorage.setItem('safeway_access_token', `mock-${newRole}-token`);
  };

  const role = user?.role || 'viewer';
  const isAdmin = role === 'admin';
  const isOperator = role === 'operator' || isAdmin;
  const isViewer = Boolean(user);

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAuthenticated: Boolean(user),
        isLoading,
        login,
        logout,
        switchRole,
        isAdmin,
        isOperator,
        isViewer,
        canManageCameras: isAdmin || role === 'operator',
        canEditSettings: isAdmin,
        canVerifyIncidents: isOperator,
        canTriggerNotifications: isOperator,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
