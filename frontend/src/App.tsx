import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SettingsProvider } from './context/SettingsContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { IncidentProvider } from './context/IncidentContext';
import { CameraProvider } from './context/CameraContext';

import { Header } from './components/common/Header';
import { Sidebar, PageId } from './components/common/Sidebar';
import { MaintenanceBanner } from './components/common/MaintenanceBanner';
import { ToastContainer } from './components/common/ToastContainer';
import { DemoSimulatorModal } from './components/common/DemoSimulatorModal';

import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { CameraManagementPage } from './pages/CameraManagementPage';
import { IncidentListPage } from './pages/IncidentListPage';
import { IncidentDetailPage } from './pages/IncidentDetailPage';
import { AccidentMapPage } from './pages/AccidentMapPage';
import { HospitalManagementPage } from './pages/HospitalManagementPage';
import { NotificationControlPage } from './pages/NotificationControlPage';
import { AdminSettingsPage } from './pages/AdminSettingsPage';

const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState<PageId | 'incident_detail'>('dashboard');
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState<boolean>(false);

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setCurrentPage('dashboard')} />;
  }

  const handleSelectIncident = (id: string) => {
    setSelectedIncidentId(id);
    setCurrentPage('incident_detail');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <DashboardPage
            onNavigate={(page) => setCurrentPage(page)}
            onSelectIncident={handleSelectIncident}
          />
        );
      case 'monitoring':
        return <LiveMonitoringPage onSelectIncident={handleSelectIncident} />;
      case 'cameras':
        return <CameraManagementPage />;
      case 'incidents':
        return <IncidentListPage onSelectIncident={handleSelectIncident} />;
      case 'incident_detail':
        return (
          <IncidentDetailPage
            incidentId={selectedIncidentId || ''}
            onBack={() => setCurrentPage('incidents')}
            onNavigate={(page) => setCurrentPage(page)}
          />
        );
      case 'map':
        return <AccidentMapPage onSelectIncident={handleSelectIncident} />;
      case 'hospitals':
        return <HospitalManagementPage />;
      case 'notifications':
        return <NotificationControlPage />;
      case 'admin':
        return <AdminSettingsPage />;
      default:
        return (
          <DashboardPage
            onNavigate={(page) => setCurrentPage(page)}
            onSelectIncident={handleSelectIncident}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col font-sans selection:bg-red-500 selection:text-white">
      {/* Top Maintenance Banner */}
      <MaintenanceBanner />

      {/* Global Command Header */}
      <Header onOpenDemoGenerator={() => setIsDemoModalOpen(true)} />

      {/* Main Workspace Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar
          activePage={currentPage === 'incident_detail' ? 'incidents' : (currentPage as PageId)}
          onNavigate={(page) => setCurrentPage(page)}
        />

        {/* Dynamic Page Container */}
        <main className="flex-1 p-4 md:p-6 lg:p-8 overflow-y-auto max-h-[calc(100vh-4rem)]">
          {renderPage()}
        </main>
      </div>

      {/* Floating Live Real-time Toasts */}
      <ToastContainer onSelectIncident={handleSelectIncident} />

      {/* Demo AI Event Simulation Modal */}
      <DemoSimulatorModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <SettingsProvider>
        <WebSocketProvider>
          <IncidentProvider>
            <CameraProvider>
              <AppContent />
            </CameraProvider>
          </IncidentProvider>
        </WebSocketProvider>
      </SettingsProvider>
    </AuthProvider>
  );
}

export default App;
