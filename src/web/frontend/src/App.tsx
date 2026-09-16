import React, { useEffect, useState } from 'react';
import { Header } from './components/layout/Header';
import { QuickActionBar } from './components/layout/QuickActionBar';
import { SystemStatusBar } from './components/dashboard/SystemStatusBar';
import { ActiveRequests } from './components/dashboard/ActiveRequests';
import { SourceAvailability } from './components/dashboard/SourceAvailability';
import { DownloadHistory } from './components/dashboard/DownloadHistory';
import { CreateRequestModal } from './components/modals/CreateRequestModal';
import { RequestDetailModal } from './components/modals/RequestDetailModal';
import { LoginPage } from './components/auth/LoginPage';
import type { DownloadRequest, EnmSource, SystemMetrics, AuthUser } from './types/dashboard';
import { apiService } from './services/api';
import { CheckCircle2, Database, Info, Loader2 } from 'lucide-react';

const defaultMetrics: SystemMetrics = {
  activeSources: 0,
  totalSources: 0,
  queueFiles: 0,
  queueUnit: '0 files',
  loadLevel: 'Moderate',
  cpuUsagePct: 0,
  memoryUsagePct: 0,
  throughputRate: '0 files/min',
};

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState<boolean>(true);

  const [metrics, setMetrics] = useState<SystemMetrics>(defaultMetrics);
  const [sources, setSources] = useState<EnmSource[]>([]);
  const [requests, setRequests] = useState<DownloadRequest[]>([]);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<string>(new Date().toLocaleTimeString());
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  
  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [detailRequest, setDetailRequest] = useState<DownloadRequest | null>(null);

  // Toast feedback state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  const showToast = (message: string, type: 'success' | 'info' = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 3500);
  };

  // 1. Initial auth check
  useEffect(() => {
    const checkAuth = async () => {
      setIsCheckingAuth(true);
      const token = localStorage.getItem('vtnet_token');
      if (token) {
        try {
          const user = await apiService.getMe();
          setCurrentUser(user);
          await loadBackendData();
        } catch (e) {
          console.warn('Stored token invalid or expired:', e);
          apiService.logout();
          setCurrentUser(null);
        }
      } else {
        setCurrentUser(null);
      }
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, []);

  // 2. Load 100% real data from backend & database
  const loadBackendData = async () => {
    const isHealthy = await apiService.checkHealth();
    setBackendConnected(isHealthy);

    if (isHealthy) {
      try {
        const [apiMetrics, apiSources, apiRequests] = await Promise.all([
          apiService.getSystemMetrics(),
          apiService.getSources(),
          apiService.getRequests(),
        ]);

        setMetrics(apiMetrics);
        setSources(apiSources);
        setRequests(apiRequests);
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (err) {
        console.error('Error loading real database data from backend:', err);
        showToast('Không thể kết nối máy chủ database. Vui lòng kiểm tra backend.', 'info');
      }
    }
  };

  // 3. Telemetry tick (sync with backend)
  const performTelemetryTick = async () => {
    if (!currentUser) return;
    setLastUpdated(new Date().toLocaleTimeString());

    try {
      const [apiMetrics, apiRequests] = await Promise.all([
        apiService.getSystemMetrics(),
        apiService.getRequests(),
      ]);
      setMetrics(apiMetrics);
      setRequests(apiRequests);
    } catch (e) {
      console.warn('Telemetry tick sync error:', e);
    }
  };

  // Auto-refresh timer
  useEffect(() => {
    if (!isAutoRefreshing || !currentUser) return;
    const interval = setInterval(performTelemetryTick, 6000);
    return () => clearInterval(interval);
  }, [isAutoRefreshing, currentUser]);

  // 4. Handler: Login success
  const handleLoginSuccess = async (user: AuthUser) => {
    setCurrentUser(user);
    showToast(`Xin chào ${user.username} (${user.role})! Kết nối Database thành công.`);
    await loadBackendData();
  };

  // 5. Handler: Logout
  const handleLogout = () => {
    apiService.logout();
    setCurrentUser(null);
    setSources([]);
    setRequests([]);
    showToast('Đã đăng xuất khỏi hệ thống VTNet.', 'info');
  };

  // 6. Handler: Create new request (Saves to backend PostgreSQL database!)
  const handleCreateRequest = async (newReqData: Partial<DownloadRequest>) => {
    try {
      const createdItem = await apiService.createRequest(newReqData);
      if (createdItem) {
        setRequests((prev) => [createdItem, ...prev]);
        showToast(`Yêu cầu ${createdItem.id} đã được lưu vào cơ sở dữ liệu PostgreSQL cho nguồn ${createdItem.sourceId}!`);
        // Refresh metrics to reflect new DB state
        apiService.getSystemMetrics().then(setMetrics).catch(() => {});
      } else {
        showToast('Không thể lưu yêu cầu vào cơ sở dữ liệu.', 'info');
      }
    } catch (err) {
      console.error('Submit error:', err);
      showToast('Lỗi khi gửi yêu cầu tới backend.', 'info');
    }
  };

  // 7. Handler: View / Toggle request status
  const handleToggleStatus = (id: string) => {
    setRequests((prev) =>
      prev.map((r) => {
        if (r.id === id) {
          if (r.status === 'SCHEDULED') {
            return {
              ...r,
              status: 'DOWNLOADING',
              progress: 15,
              downloadSpeed: '58.2 MB/s',
              eta: '1m 45s remaining',
            };
          }
          if (r.status === 'DOWNLOADING') {
            return {
              ...r,
              status: 'COMPLETED',
              progress: 100,
              eta: 'Finished',
              downloadSpeed: 'Completed',
            };
          }
          if (r.status === 'COMPLETED') {
            return {
              ...r,
              status: 'SCHEDULED',
              progress: 0,
              eta: 'Re-queued',
            };
          }
        }
        return r;
      })
    );
    setDetailRequest(null);
    showToast(`Request ${id} status updated.`);
  };

  // Loading screen while checking stored token
  if (isCheckingAuth) {
    return (
      <div style={{
        minHeight: '100vh',
        width: '100%',
        backgroundColor: '#020617',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#38BDF8',
        gap: '1rem',
        fontFamily: 'Inter, sans-serif'
      }}>
        <Loader2 className="animate-spin" size={36} />
        <span style={{ fontSize: '0.9rem', color: '#94A3B8' }}>Đang kết nối hệ thống VTNet...</span>
      </div>
    );
  }

  // If not logged in, render LoginPage
  if (!currentUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <main className="app-container">
      {/* Toast Notification Banner */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: '1.5rem',
          right: '2rem',
          zIndex: 9999,
          background: 'rgba(15, 23, 42, 0.95)',
          border: '1px solid rgba(56, 189, 248, 0.4)',
          borderRadius: '10px',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
          padding: '0.75rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          color: '#F8FAFC',
          fontSize: '0.85rem',
          animation: 'fadeIn 0.2s ease-out'
        }}>
          {toast.type === 'success' ? (
            <CheckCircle2 size={18} color="#10B981" />
          ) : (
            <Info size={18} color="#38BDF8" />
          )}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Backend Connectivity Status Badge */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.4rem 1rem',
        borderRadius: '8px',
        background: backendConnected ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
        border: `1px solid ${backendConnected ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
        fontSize: '0.75rem',
        color: backendConnected ? '#34D399' : '#FBBF24'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Database size={13} />
          <span>
            Backend API: <strong>{backendConnected ? 'Connected (http://127.0.0.1:8000)' : 'Connecting to Backend...'}</strong>
          </span>
          <span style={{ color: '#64748B' }}>• PostgreSQL (port 5433 / vtnet)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span className={`pulse-dot ${backendConnected ? 'green' : 'amber'}`} style={{ width: '6px', height: '6px' }}></span>
          <span>{backendConnected ? `Live Database Online (${sources.length} Sources loaded)` : 'Standby Mode'}</span>
        </div>
      </div>

      {/* 1. Header (Dashboard ... User) */}
      <Header
        lastUpdated={lastUpdated}
        isAutoRefreshing={isAutoRefreshing}
        currentUser={currentUser}
        onLogout={handleLogout}
        onRefresh={() => {
          loadBackendData();
          performTelemetryTick();
        }}
      />

      {/* 2. Action Bar (+ Create Download Request) */}
      <QuickActionBar
        onCreateClick={() => setIsCreateModalOpen(true)}
        isAutoRefreshing={isAutoRefreshing}
        onToggleAutoRefresh={() => setIsAutoRefreshing(!isAutoRefreshing)}
        onSimulateTick={performTelemetryTick}
      />

      {/* 3. System Status (6 / 10 sources active   Queue: 32k files   Load: Moderate) */}
      <SystemStatusBar metrics={metrics} />

      {/* 4. Two-Column layout matching layout2.md */}
      <div className="dashboard-grid-two-col">
        {/* Left Column: My Active Requests */}
        <ActiveRequests
          requests={requests}
          onRequestClick={(req) => setDetailRequest(req)}
        />

        {/* Right Column: Source Availability */}
        <SourceAvailability
          sources={sources}
          onSelectSource={(source) => {
            showToast(`Selected source ${source.id} (${source.status})`, 'info');
          }}
        />
      </div>

      {/* 5. Full-width: Recent Download History / Download Request History */}
      <DownloadHistory
        requests={requests}
        onRequestClick={(req) => setDetailRequest(req)}
      />

      {/* Create Download Request Modal */}
      <CreateRequestModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        sources={sources}
        onCreate={handleCreateRequest}
      />

      {/* Request Detail & Log Modal */}
      <RequestDetailModal
        request={detailRequest}
        onClose={() => setDetailRequest(null)}
        onToggleStatus={handleToggleStatus}
      />
    </main>
  );
};

export default App;
