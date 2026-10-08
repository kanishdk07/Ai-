import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Camera, CameraType, CameraStatus } from '../types';
import { cameraApi } from '../api/cameraApi';

interface CameraContextType {
  cameras: Camera[];
  selectedCamera: Camera | null;
  onlineCount: number;
  monitoringCount: number;
  offlineCount: number;
  isLoading: boolean;
  filterType: string;
  setFilterType: (t: string) => void;
  setSelectedCamera: (cam: Camera | null) => void;
  fetchCameras: () => Promise<void>;
  createCamera: (data: Partial<Camera>) => Promise<Camera>;
  updateCamera: (id: string, data: Partial<Camera>) => Promise<Camera>;
  startMonitoring: (id: string) => Promise<void>;
  stopMonitoring: (id: string) => Promise<void>;
  deleteCamera: (id: string) => Promise<void>;
}

const CameraContext = createContext<CameraContextType | undefined>(undefined);

export const CameraProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [filterType, setFilterType] = useState<string>('all');

  const fetchCameras = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await cameraApi.getCameras();
      setCameras(res.cameras);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const createCamera = async (data: Partial<Camera>) => {
    const created = await cameraApi.createCamera(data);
    setCameras((prev) => [created, ...prev]);
    return created;
  };

  const updateCamera = async (id: string, data: Partial<Camera>) => {
    const updated = await cameraApi.updateCamera(id, data);
    setCameras((prev) => prev.map((c) => (c.id === id ? updated : c)));
    if (selectedCamera?.id === id) setSelectedCamera(updated);
    return updated;
  };

  const startMonitoring = async (id: string) => {
    const updated = await cameraApi.startMonitoring(id);
    setCameras((prev) => prev.map((c) => (c.id === id ? updated : c)));
    if (selectedCamera?.id === id) setSelectedCamera(updated);
  };

  const stopMonitoring = async (id: string) => {
    const updated = await cameraApi.stopMonitoring(id);
    setCameras((prev) => prev.map((c) => (c.id === id ? updated : c)));
    if (selectedCamera?.id === id) setSelectedCamera(updated);
  };

  const deleteCamera = async (id: string) => {
    await cameraApi.deleteCamera(id);
    setCameras((prev) => prev.filter((c) => c.id !== id));
    if (selectedCamera?.id === id) setSelectedCamera(null);
  };

  const onlineCount = cameras.filter((c) => c.status === 'online' || c.status === 'monitoring').length;
  const monitoringCount = cameras.filter((c) => c.is_monitoring).length;
  const offlineCount = cameras.filter((c) => c.status === 'offline' || c.status === 'error').length;

  return (
    <CameraContext.Provider
      value={{
        cameras,
        selectedCamera,
        onlineCount,
        monitoringCount,
        offlineCount,
        isLoading,
        filterType,
        setFilterType,
        setSelectedCamera,
        fetchCameras,
        createCamera,
        updateCamera,
        startMonitoring,
        stopMonitoring,
        deleteCamera,
      }}
    >
      {children}
    </CameraContext.Provider>
  );
};

export const useCameras = () => {
  const context = useContext(CameraContext);
  if (!context) throw new Error('useCameras must be used within a CameraProvider');
  return context;
};
