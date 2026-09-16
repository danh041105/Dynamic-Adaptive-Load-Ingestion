import { ArrowRight, Clock, Radio } from 'lucide-react';
import type { DownloadRequest } from '../../types/dashboard';

interface ActiveRequestsProps {
  requests: DownloadRequest[];
  onRequestClick: (req: DownloadRequest) => void;
  onAbortRequest?: (id: string) => void;
}

export const ActiveRequests: React.FC<ActiveRequestsProps> = ({
  requests,
  onRequestClick,
}) => {
  // Filter active requests (SCHEDULED, RUNNING, DOWNLOADING)
  const activeList = requests.filter(
    r => r.status === 'SCHEDULED' || r.status === 'RUNNING' || r.status === 'DOWNLOADING'
  );

  return (
    <section className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
      {/* Title matching layout2.md: "My Active Requests" */}
      <div className="section-title-row">
        <div className="section-title">
          <Radio size={18} color="#38BDF8" />
          <span>My Active Requests</span>
        </div>
        <span className="section-badge mono-data">
          {activeList.length} In Progress
        </span>
      </div>

      {activeList.length === 0 ? (
        <div style={{ padding: '2rem 1rem', textAlign: 'center', color: '#64748B' }}>
          <Clock size={28} style={{ opacity: 0.5, marginBottom: '0.5rem' }} />
          <p>No active requests running at the moment.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {activeList.map((req) => {
            const isRunning = req.status === 'RUNNING' || req.status === 'DOWNLOADING';
            const isScheduled = req.status === 'SCHEDULED';

            return (
              <div
                key={req.id}
                onClick={() => onRequestClick(req)}
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: `1px solid ${isRunning ? 'rgba(16, 185, 129, 0.25)' : 'rgba(56, 189, 248, 0.25)'}`,
                  borderRadius: '12px',
                  padding: '1rem 1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = isRunning ? '#10B981' : '#38BDF8';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = isRunning ? 'rgba(16, 185, 129, 0.25)' : 'rgba(56, 189, 248, 0.25)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                }}
              >
                {/* Main line matching layout2.md: "#105 ENM06  10:00 → 12:00  SCHEDULED" */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '0.75rem'
                }}>
                  {/* ID and Source */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span className="mono-data" style={{
                      fontWeight: 700,
                      fontSize: '1rem',
                      color: '#F8FAFC',
                      background: 'rgba(255, 255, 255, 0.08)',
                      padding: '0.2rem 0.6rem',
                      borderRadius: '6px'
                    }}>
                      {req.id}
                    </span>
                    <span className="mono-data" style={{
                      fontSize: '1rem',
                      fontWeight: 700,
                      color: '#38BDF8'
                    }}>
                      {req.sourceId}
                    </span>
                  </div>

                  {/* Time Window: "10:00 → 12:00" */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#94A3B8', fontSize: '0.9rem' }}>
                    <Clock size={15} color="#64748B" />
                    <span className="mono-data" style={{ fontWeight: 600, color: '#F1F5F9' }}>
                      {req.timeWindow.start}
                    </span>
                    <ArrowRight size={14} color="#64748B" />
                    <span className="mono-data" style={{ fontWeight: 600, color: '#F1F5F9' }}>
                      {req.timeWindow.end}
                    </span>
                  </div>

                  {/* Status Pill: SCHEDULED / RUNNING */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`status-pill ${isRunning ? 'status-running' : 'status-scheduled'}`}>
                      {isRunning ? (
                        <>
                          <span className="pulse-dot green" style={{ width: '6px', height: '6px' }}></span>
                          <span>RUNNING</span>
                        </>
                      ) : (
                        <>
                          <Clock size={12} />
                          <span>SCHEDULED</span>
                        </>
                      )}
                    </span>
                  </div>
                </div>

                {/* Progress bar and details for RUNNING items (e.g. #104) */}
                {isRunning && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94A3B8' }}>
                      <span>Progress: <strong style={{ color: '#10B981' }} className="mono-data">{req.progress}%</strong></span>
                      <span className="mono-data">{req.downloadSpeed || '45 MB/s'} • {req.eta || 'Calculating...'}</span>
                    </div>
                    <div className="progress-track">
                      <div
                        className="progress-fill active"
                        style={{ width: `${req.progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Scheduled details (e.g. #105) */}
                {isScheduled && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748B' }}>
                    <span>Type: <strong style={{ color: '#94A3B8' }}>{req.dataType || 'Cell Trace'}</strong></span>
                    <span className="mono-data" style={{ color: '#38BDF8' }}>{req.eta || 'Queued for trigger'}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
