import React from 'react';
import { Play, Plus, RefreshCw, Zap } from 'lucide-react';

interface QuickActionBarProps {
  onCreateClick: () => void;
  isAutoRefreshing: boolean;
  onToggleAutoRefresh: () => void;
  onSimulateTick: () => void;
}

export const QuickActionBar: React.FC<QuickActionBarProps> = ({
  onCreateClick,
  isAutoRefreshing,
  onToggleAutoRefresh,
  onSimulateTick,
}) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '0.75rem',
      padding: '0.25rem 0',
    }}>
      {/* Primary Action matching layout2.md: "+ Create Download Request" */}
      <button
        onClick={onCreateClick}
        className="btn-primary"
        style={{ fontSize: '0.95rem', padding: '0.75rem 1.4rem' }}
        id="btn-create-download-request"
      >
        <Plus size={18} strokeWidth={2.5} />
        <span>Create Download Request</span>
      </button>

      {/* Real-time simulation bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <button
          onClick={onSimulateTick}
          className="btn-secondary"
          title="Simulate incremental download progress & queue updates"
          style={{ background: 'rgba(56, 189, 248, 0.08)', color: '#38BDF8', borderColor: 'rgba(56, 189, 248, 0.25)' }}
        >
          <Zap size={14} />
          <span>Advance Simulation Step</span>
        </button>

        <button
          onClick={onToggleAutoRefresh}
          className="btn-secondary"
          style={{
            background: isAutoRefreshing ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.05)',
            borderColor: isAutoRefreshing ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-card)',
            color: isAutoRefreshing ? '#10B981' : '#94A3B8'
          }}
        >
          {isAutoRefreshing ? (
            <>
              <RefreshCw size={14} className="spin-slow" />
              <span>Live Auto-Sync: Active (3s)</span>
            </>
          ) : (
            <>
              <Play size={14} />
              <span>Resume Auto-Sync</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
