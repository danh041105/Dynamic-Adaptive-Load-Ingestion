import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, Clock, FileSpreadsheet, History, Search, Inbox } from 'lucide-react';
import type { DownloadRequest, RequestStatus } from '../../types/dashboard';

interface DownloadHistoryProps {
  requests: DownloadRequest[];
  onRequestClick: (req: DownloadRequest) => void;
}

export const DownloadHistory: React.FC<DownloadHistoryProps> = ({
  requests,
  onRequestClick,
}) => {
  const [statusFilter, setStatusFilter] = useState<'ALL' | RequestStatus>('ALL');
  const [search, setSearch] = useState('');

  const filtered = requests.filter((r) => {
    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    const matchesSearch =
      r.id.toLowerCase().includes(search.toLowerCase()) ||
      r.sourceId.toLowerCase().includes(search.toLowerCase()) ||
      (r.dataType && r.dataType.toLowerCase().includes(search.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  return (
    <section className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
      
      {/* Title 1 matching layout2.md: "Recent Download History" */}
      <div className="section-title-row">
        <div className="section-title">
          <History size={18} color="#38BDF8" />
          <span>Recent Download History</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            className="btn-secondary"
            onClick={() => alert('Exporting download history manifest...')}
            title="Export CSV audit log"
          >
            <FileSpreadsheet size={14} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Title 2 / Table Section matching layout2.md: "Download Request History" */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1rem',
        paddingTop: '0.25rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#E2E8F0' }}>
            Download Request History
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
            ({filtered.length} requests logged in Database)
          </span>
        </div>

        {/* Search & Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '6px',
            padding: '0.3rem 0.6rem',
          }}>
            <Search size={13} color="#64748B" />
            <input
              type="text"
              placeholder="Search #ID, ENM..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#F8FAFC',
                fontSize: '0.75rem',
                outline: 'none',
                width: '120px'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '4px' }}>
            {(['ALL', 'SCHEDULED', 'DOWNLOADING', 'COMPLETED'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  fontSize: '0.7rem',
                  padding: '0.25rem 0.55rem',
                  borderRadius: '6px',
                  fontWeight: 500,
                  background: statusFilter === st ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  color: statusFilter === st ? '#38BDF8' : '#94A3B8',
                  border: statusFilter === st ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid rgba(255, 255, 255, 0.05)',
                }}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Table matching wireframe */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '80px' }}>Request ID</th>
              <th>Source</th>
              <th>Time Window</th>
              <th>Data Type</th>
              <th>Status / Progress</th>
              <th>Files & Volume</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem 1rem', color: '#64748B' }}>
                  <Inbox size={28} style={{ opacity: 0.4, margin: '0 auto 0.5rem auto' }} />
                  <p style={{ margin: 0, fontSize: '0.85rem' }}>Chưa có yêu cầu download nào trong cơ sở dữ liệu.</p>
                  <span style={{ fontSize: '0.75rem', color: '#475569' }}>Nhấp "+ Create Download Request" ở thanh thao tác để tạo yêu cầu mới.</span>
                </td>
              </tr>
            ) : (
              filtered.map((req) => {
                const isScheduled = req.status === 'SCHEDULED';
                const isDownloading = req.status === 'DOWNLOADING' || req.status === 'RUNNING';

                return (
                  <tr
                    key={req.id}
                    onClick={() => onRequestClick(req)}
                    style={{ cursor: 'pointer' }}
                  >
                    {/* Request ID (e.g. #105, #104, #103) */}
                    <td className="mono-data" style={{ fontWeight: 700, color: '#F8FAFC' }}>
                      <span style={{
                        background: 'rgba(255, 255, 255, 0.06)',
                        padding: '0.15rem 0.45rem',
                        borderRadius: '4px'
                      }}>
                        {req.id}
                      </span>
                    </td>

                    {/* Source (e.g. ENM06, ENM03, ENM02) */}
                    <td className="mono-data" style={{ fontWeight: 600, color: '#38BDF8' }}>
                      {req.sourceId}
                    </td>

                    {/* Time Window (e.g. 10:00 -> 12:00) */}
                    <td className="mono-data">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#CBD5E1' }}>
                        <Clock size={13} color="#64748B" />
                        <span>{req.timeWindow.start}</span>
                        <ArrowRight size={11} color="#64748B" />
                        <span>{req.timeWindow.end}</span>
                      </div>
                    </td>

                    {/* Data Type */}
                    <td style={{ color: '#94A3B8', fontSize: '0.8rem' }}>
                      {req.dataType || 'Cell Trace'}
                    </td>

                    {/* Status / Progress (e.g. SCHEDULED, DOWNLOADING 65%, COMPLETED) */}
                    <td style={{ minWidth: '180px' }}>
                      {isDownloading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span className="status-pill status-downloading">
                              <span className="pulse-dot cyan" style={{ width: '6px', height: '6px' }}></span>
                              <span>DOWNLOADING</span>
                            </span>
                            <span className="mono-data" style={{ fontWeight: 700, color: '#38BDF8', fontSize: '0.85rem' }}>
                              {req.progress}%
                            </span>
                          </div>
                          <div className="progress-track" style={{ height: '5px' }}>
                            <div
                              className="progress-fill active"
                              style={{ width: `${req.progress}%` }}
                            />
                          </div>
                        </div>
                      ) : isScheduled ? (
                        <span className="status-pill status-scheduled">
                          <Clock size={11} />
                          <span>SCHEDULED</span>
                        </span>
                      ) : (
                        <span className="status-pill status-completed">
                          <CheckCircle2 size={11} />
                          <span>COMPLETED</span>
                        </span>
                      )}
                    </td>

                    {/* Files & Volume */}
                    <td className="mono-data" style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
                      {req.fileCount ? (
                        <div>
                          <span style={{ color: '#F1F5F9', fontWeight: 600 }}>{req.fileCount.toLocaleString()}</span> files
                          <span style={{ color: '#64748B' }}> ({Math.round(req.totalSizeMb || 0)} MB)</span>
                        </div>
                      ) : (
                        <span style={{ color: '#64748B' }}>Pending capture</span>
                      )}
                    </td>

                    {/* Action */}
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn-secondary"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onRequestClick(req);
                        }}
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
};
