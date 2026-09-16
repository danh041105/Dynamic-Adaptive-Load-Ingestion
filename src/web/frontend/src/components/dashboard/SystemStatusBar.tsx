import React from 'react';
import { Activity, Cpu, Layers, Server } from 'lucide-react';
import type { SystemMetrics } from '../../types/dashboard';

interface SystemStatusBarProps {
  metrics: SystemMetrics;
}

export const SystemStatusBar: React.FC<SystemStatusBarProps> = ({ metrics }) => {
  const activePercentage = Math.round((metrics.activeSources / metrics.totalSources) * 100);

  return (
    <section className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
      {/* Title matching layout2.md */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Activity size={18} color="#38BDF8" />
          <h2 style={{ fontSize: '1rem', fontWeight: 700, letterSpacing: '-0.01em', color: '#F8FAFC' }}>
            System Status
          </h2>
          <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>• Real-time Telemetry Engine</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: '#10B981' }}>
          <span className="pulse-dot green"></span>
          <span>Cluster Operational</span>
        </div>
      </div>

      {/* The 3 Core Telemetry Items from layout2.md */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.25rem',
      }}>
        
        {/* Metric 1: 6 / 10 sources active */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Sources Active
            </span>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.12)',
              color: '#10B981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Server size={16} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
              <span className="mono-data" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#F8FAFC' }}>
                {metrics.activeSources} / {metrics.totalSources}
              </span>
              <span style={{ fontSize: '0.9rem', color: '#10B981', fontWeight: 600 }}>
                sources active
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>
              4 Available • 2 Busy • 2 Offline / Standby
            </p>
          </div>

          <div className="progress-track" style={{ height: '6px' }}>
            <div
              className="progress-fill"
              style={{
                width: `${activePercentage}%`,
                background: 'linear-gradient(90deg, #10B981 0%, #34D399 100%)',
                boxShadow: '0 0 10px rgba(16, 185, 129, 0.4)'
              }}
            />
          </div>
        </div>

        {/* Metric 2: Queue: 32k files */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Ingestion Queue
            </span>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.12)',
              color: '#38BDF8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Layers size={16} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
              <span style={{ fontSize: '1rem', color: '#94A3B8', fontWeight: 500 }}>Queue:</span>
              <span className="mono-data" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38BDF8' }}>
                {metrics.queueUnit}
              </span>
            </div>
            <p className="mono-data" style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>
              Raw count: {metrics.queueFiles.toLocaleString()} files • {metrics.throughputRate}
            </p>
          </div>

          {/* Simulated sparkline visualization */}
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '14px', paddingTop: '2px' }}>
            {[35, 45, 40, 60, 55, 75, 70, 85, 80, 90, 78, 85, 95, 92, 88].map((h, i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: `${h}%`,
                  background: i === 14 ? '#38BDF8' : 'rgba(56, 189, 248, 0.35)',
                  borderRadius: '2px'
                }}
              />
            ))}
          </div>
        </div>

        {/* Metric 3: Load: Moderate */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Cluster Workload
            </span>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.12)',
              color: '#F59E0B',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Cpu size={16} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
              <span style={{ fontSize: '1rem', color: '#94A3B8', fontWeight: 500 }}>Load:</span>
              <span style={{
                fontSize: '1.75rem',
                fontWeight: 800,
                color: metrics.loadLevel === 'Moderate' ? '#F59E0B' : metrics.loadLevel === 'Low' ? '#10B981' : '#EF4444'
              }}>
                {metrics.loadLevel}
              </span>
            </div>
            <p className="mono-data" style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>
              CPU: {metrics.cpuUsagePct}% • Memory: {metrics.memoryUsagePct}% (Balanced)
            </p>
          </div>

          <div className="progress-track" style={{ height: '6px' }}>
            <div
              className="progress-fill"
              style={{
                width: `${metrics.cpuUsagePct}%`,
                background: 'linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%)',
                boxShadow: '0 0 10px rgba(245, 158, 11, 0.4)'
              }}
            />
          </div>
        </div>

      </div>
    </section>
  );
};
