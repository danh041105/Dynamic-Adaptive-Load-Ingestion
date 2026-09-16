import React, { useState } from 'react';
import { Search, Server, Wifi } from 'lucide-react';
import type { EnmSource, SourceStatus } from '../../types/dashboard';

interface SourceAvailabilityProps {
  sources: EnmSource[];
  onSelectSource?: (source: EnmSource) => void;
}

export const SourceAvailability: React.FC<SourceAvailabilityProps> = ({
  sources,
  onSelectSource,
}) => {
  const [filter, setFilter] = useState<'ALL' | SourceStatus>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSources = sources.filter((s) => {
    const matchesFilter = filter === 'ALL' || s.status === filter;
    const matchesSearch =
      s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.vendor.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <section className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
      {/* Title matching layout2.md: "Source Availability" */}
      <div className="section-title-row">
        <div className="section-title">
          <Server size={18} color="#10B981" />
          <span>Source Availability</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="section-badge mono-data">
            {sources.filter(s => s.status === 'Available').length} Available / {sources.length} Total
          </span>
        </div>
      </div>

      {/* Quick Search and Filter Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1rem'
      }}>
        {/* Search */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          padding: '0.35rem 0.75rem',
          maxWidth: '220px',
          flex: 1
        }}>
          <Search size={14} color="#64748B" />
          <input
            type="text"
            placeholder="Filter source ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#F8FAFC',
              fontSize: '0.8rem',
              width: '100%',
              outline: 'none'
            }}
          />
        </div>

        {/* Status Pills Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          {(['ALL', 'Available', 'Busy', 'Offline'] as const).map((statusKey) => (
            <button
              key={statusKey}
              onClick={() => setFilter(statusKey)}
              style={{
                fontSize: '0.75rem',
                padding: '0.25rem 0.6rem',
                borderRadius: '6px',
                fontWeight: 500,
                background: filter === statusKey ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                color: filter === statusKey ? '#38BDF8' : '#94A3B8',
                border: filter === statusKey ? '1px solid rgba(56, 189, 248, 0.35)' : '1px solid rgba(255, 255, 255, 0.05)',
              }}
            >
              {statusKey}
            </button>
          ))}
        </div>
      </div>

      {/* Sources List / Grid matching layout2.md */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: '0.75rem',
        maxHeight: '340px',
        overflowY: 'auto',
        paddingRight: '4px'
      }}>
        {filteredSources.map((source) => {
          const isAvailable = source.status === 'Available';
          const isBusy = source.status === 'Busy';

          return (
            <div
              key={source.id}
              onClick={() => onSelectSource?.(source)}
              style={{
                background: 'rgba(255, 255, 255, 0.025)',
                border: `1px solid ${isAvailable ? 'rgba(16, 185, 129, 0.2)' : isBusy ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
                borderRadius: '10px',
                padding: '0.85rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.025)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              {/* Row matching layout2.md: "ENM01 Available", "ENM02 Busy", "ENM03 Available" */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="mono-data" style={{ fontWeight: 700, fontSize: '1rem', color: '#F8FAFC' }}>
                  {source.id}
                </span>

                <span className={`status-pill ${
                  isAvailable ? 'status-available' : isBusy ? 'status-busy' : 'status-offline'
                }`}>
                  <span className={`pulse-dot ${isAvailable ? 'green' : isBusy ? 'amber' : ''}`}></span>
                  <span>{source.status}</span>
                </span>
              </div>

              {/* Subtitle / Region & Latency */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748B' }}>
                <span>{source.region}</span>
                <span className="mono-data" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Wifi size={11} color={isAvailable ? '#10B981' : isBusy ? '#F59E0B' : '#64748B'} />
                  {source.latencyMs > 0 ? `${source.latencyMs}ms` : 'Timeout'}
                </span>
              </div>

              {/* Active task load indicator */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.7rem', color: '#94A3B8' }}>
                <span style={{ minWidth: '60px' }}>Load:</span>
                <div className="progress-track" style={{ height: '4px' }}>
                  <div
                    className="progress-fill"
                    style={{
                      width: `${(source.activeTasks / source.maxTasks) * 100}%`,
                      background: isBusy ? '#F59E0B' : '#10B981'
                    }}
                  />
                </div>
                <span className="mono-data">{source.activeTasks}/{source.maxTasks}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
