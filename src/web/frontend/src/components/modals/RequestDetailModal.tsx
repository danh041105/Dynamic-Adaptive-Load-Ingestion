import React from 'react';
import { ArrowRight, Clock, Terminal, X, Zap } from 'lucide-react';
import type { DownloadRequest } from '../../types/dashboard';

interface RequestDetailModalProps {
  request: DownloadRequest | null;
  onClose: () => void;
  onToggleStatus?: (id: string) => void;
}

export const RequestDetailModal: React.FC<RequestDetailModalProps> = ({
  request,
  onClose,
  onToggleStatus,
}) => {
  if (!request) return null;

  const isRunning = request.status === 'RUNNING' || request.status === 'DOWNLOADING';
  const isScheduled = request.status === 'SCHEDULED';
  const isCompleted = request.status === 'COMPLETED';

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-dialog"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-detail-title"
        style={{ maxWidth: '640px' }}
      >
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255, 255, 255, 0.02)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="mono-data" style={{
              fontSize: '1.2rem',
              fontWeight: 800,
              color: '#F8FAFC',
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '0.2rem 0.6rem',
              borderRadius: '6px'
            }}>
              {request.id}
            </span>
            <div>
              <h2 id="modal-detail-title" style={{ fontSize: '1.1rem', fontWeight: 700, color: '#F8FAFC' }}>
                Download Request Details
              </h2>
              <span className="mono-data" style={{ fontSize: '0.8rem', color: '#38BDF8', fontWeight: 600 }}>
                Target Source: {request.sourceId}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close details dialog"
            style={{ color: '#94A3B8', padding: '0.4rem', borderRadius: '6px' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Progress Bar if downloading */}
          {isRunning && (
            <div style={{
              padding: '1rem',
              background: 'rgba(14, 165, 233, 0.08)',
              border: '1px solid rgba(14, 165, 233, 0.25)',
              borderRadius: '10px',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: '#38BDF8', fontWeight: 600 }}>Real-time Transfer Progress</span>
                <span className="mono-data" style={{ fontWeight: 700, color: '#F8FAFC' }}>{request.progress}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill active" style={{ width: `${request.progress}%` }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94A3B8' }}>
                <span>Speed: <strong className="mono-data" style={{ color: '#F8FAFC' }}>{request.downloadSpeed || '54 MB/s'}</strong></span>
                <span>ETA: <strong className="mono-data" style={{ color: '#38BDF8' }}>{request.eta || '1m 20s'}</strong></span>
              </div>
            </div>
          )}

          {/* Key Attributes Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
            background: 'rgba(255, 255, 255, 0.02)',
            padding: '1rem',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block' }}>Time Window:</span>
              <div className="mono-data" style={{ fontSize: '0.9rem', color: '#F8FAFC', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                <Clock size={13} color="#38BDF8" />
                <span>{request.timeWindow.start}</span>
                <ArrowRight size={12} />
                <span>{request.timeWindow.end}</span>
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block' }}>Current Status:</span>
              <span style={{ marginTop: '2px', display: 'inline-block' }} className={`status-pill ${
                isRunning ? 'status-running' : isScheduled ? 'status-scheduled' : 'status-completed'
              }`}>
                {request.status}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block' }}>Payload Type:</span>
              <span style={{ fontSize: '0.85rem', color: '#F8FAFC', fontWeight: 600 }}>{request.dataType || 'Cell Trace'}</span>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: '#64748B', display: 'block' }}>Estimated Files:</span>
              <span className="mono-data" style={{ fontSize: '0.85rem', color: '#F8FAFC', fontWeight: 600 }}>
                {request.fileCount ? `${request.fileCount.toLocaleString()} files (~${request.totalSizeMb} MB)` : 'Pending'}
              </span>
            </div>
          </div>

          {/* Telemetry Log Stream */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', fontSize: '0.8rem', color: '#94A3B8' }}>
              <Terminal size={14} />
              <span>Live Ingestion Worker Logs:</span>
            </div>
            <div style={{
              background: '#070B13',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              fontSize: '0.75rem',
              color: '#A5F3FC',
              fontFamily: 'var(--font-mono)',
              lineHeight: '1.6',
              maxHeight: '140px',
              overflowY: 'auto'
            }}>
              <div>[10:14:02.102] CONNECT source={request.sourceId} proto=SFTP/2.0 status=ESTABLISHED</div>
              <div>[10:14:03.450] DISCOVER batch pattern=CT_DATA_*.bin found={request.fileCount || 3420} entries</div>
              <div>[10:14:04.012] STREAM worker_id=wk-04 chunk_size=16MB crc32_verify=PASS</div>
              {isRunning && <div style={{ color: '#10B981' }}>[10:14:10.881] INGEST rate=64.2MB/s written={Math.round((request.progress / 100) * (request.totalSizeMb || 4000))}MB status=OK</div>}
              {isCompleted && <div style={{ color: '#34D399' }}>[10:14:15.000] COMPLETED checksums_verified=ALL manifest_written=DONE</div>}
            </div>
          </div>

          {/* Footer actions */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '0.5rem',
            borderTop: '1px solid rgba(255, 255, 255, 0.06)'
          }}>
            <button
              onClick={() => onToggleStatus?.(request.id)}
              className="btn-secondary"
              style={{ color: '#38BDF8', borderColor: 'rgba(56, 189, 248, 0.3)' }}
            >
              <Zap size={14} />
              <span>{isRunning ? 'Mark as Completed' : isScheduled ? 'Trigger Download Now' : 'Re-run Request'}</span>
            </button>

            <button onClick={onClose} className="btn-secondary">
              Close
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};
