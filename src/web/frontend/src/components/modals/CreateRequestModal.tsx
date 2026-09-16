import React, { useState, useEffect } from 'react';
import { AlertCircle, Check, Clock, Plus, X } from 'lucide-react';
import type { DownloadRequest, EnmSource } from '../../types/dashboard';

interface CreateRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  sources: EnmSource[];
  onCreate: (newRequest: Partial<DownloadRequest>) => void;
}

export const CreateRequestModal: React.FC<CreateRequestModalProps> = ({
  isOpen,
  onClose,
  sources,
  onCreate,
}) => {
  const [selectedSource, setSelectedSource] = useState<string>(sources[0]?.id || '');
  const [startTime, setStartTime] = useState('14:00');
  const [endTime, setEndTime] = useState('16:00');
  const [dataType, setDataType] = useState<'Cell Trace' | 'PM Counters' | 'Alarm Logs' | 'Raw PCAP'>('Cell Trace');
  const [priority, setPriority] = useState<'Low' | 'Normal' | 'High' | 'Urgent'>('Normal');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sources.length > 0 && (!selectedSource || !sources.some(s => s.id === selectedSource))) {
      setSelectedSource(sources[0].id);
    }
  }, [sources, isOpen]);

  if (!isOpen) return null;

  const currentSourceObj = sources.find(s => s.id === selectedSource);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSource && sources.length > 0) {
      setSelectedSource(sources[0].id);
    }
    const sourceTarget = selectedSource || (sources.length > 0 ? sources[0].id : 'ENM62');

    if (!startTime || !endTime) {
      setError('Please provide both Start and End times');
      return;
    }

    const found = sources.find((s) => s.id === sourceTarget || s.name === sourceTarget);
    onCreate({
      sourceId: sourceTarget,
      rawSourceId: found?.rawId,
      timeWindow: {
        start: startTime,
        end: endTime,
        date: 'Today',
      },
      dataType,
      priority,
      status: 'SCHEDULED',
      progress: 0,
      fileCount: Math.floor(Math.random() * 4000) + 1200,
      totalSizeMb: Math.floor(Math.random() * 5000) + 1500,
      eta: `Scheduled for ${startTime}`,
    });

    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose} style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(2, 6, 23, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem',
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div
        className="modal-content glass-panel"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '540px',
          background: '#0F172A',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(14, 165, 233, 0.15)',
          overflow: 'hidden',
          animation: 'scaleUp 0.25s cubic-bezier(0.16, 1, 0.3, 1)'
        }}
      >
        {/* Modal Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255, 255, 255, 0.02)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38BDF8'
            }}>
              <Plus size={18} />
            </div>
            <div>
              <h2 id="modal-create-title" style={{ fontSize: '1.1rem', fontWeight: 700, color: '#F8FAFC' }}>
                Create Download Request
              </h2>
              <p style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
                Schedule trace extraction and ingestion from radio network manager
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{ color: '#94A3B8', padding: '0.4rem', borderRadius: '6px', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {error && (
            <div style={{
              padding: '0.75rem 1rem',
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              color: '#F87171',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Source Selection */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1' }}>
              Select ENM Source Target:
            </label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '8px',
                padding: '0.65rem 0.85rem',
                color: '#F8FAFC',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            >
              {sources.map((s) => (
                <option key={s.id} value={s.id} style={{ background: '#0F172A', color: '#F8FAFC' }}>
                  {s.id} — {s.name} ({s.status}, {s.activeTasks}/{s.maxTasks} tasks)
                </option>
              ))}
            </select>
            {currentSourceObj && (
              <span style={{ fontSize: '0.75rem', color: currentSourceObj.status === 'Available' ? '#10B981' : '#F59E0B' }}>
                Status: {currentSourceObj.status} • Latency: {currentSourceObj.latencyMs}ms • IP: {currentSourceObj.ipAddress}
              </span>
            )}
          </div>

          {/* Time Window Inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} color="#38BDF8" />
                <span>Start Time (HH:MM):</span>
              </label>
              <input
                type="text"
                placeholder="10:00"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '8px',
                  padding: '0.65rem 0.85rem',
                  color: '#F8FAFC',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-mono)'
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} color="#38BDF8" />
                <span>End Time (HH:MM):</span>
              </label>
              <input
                type="text"
                placeholder="12:00"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '8px',
                  padding: '0.65rem 0.85rem',
                  color: '#F8FAFC',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-mono)'
                }}
              />
            </div>
          </div>

          {/* Data Type & Priority */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1' }}>
                Data Type:
              </label>
              <select
                value={dataType}
                onChange={(e) => setDataType(e.target.value as any)}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '8px',
                  padding: '0.65rem 0.85rem',
                  color: '#F8FAFC',
                  fontSize: '0.9rem',
                }}
              >
                <option value="Cell Trace" style={{ background: '#0F172A' }}>Cell Trace</option>
                <option value="PM Counters" style={{ background: '#0F172A' }}>PM Counters</option>
                <option value="Alarm Logs" style={{ background: '#0F172A' }}>Alarm Logs</option>
                <option value="Raw PCAP" style={{ background: '#0F172A' }}>Raw PCAP</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1' }}>
                Ingestion Priority:
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as any)}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '8px',
                  padding: '0.65rem 0.85rem',
                  color: '#F8FAFC',
                  fontSize: '0.9rem',
                }}
              >
                <option value="Normal" style={{ background: '#0F172A' }}>Normal</option>
                <option value="High" style={{ background: '#0F172A' }}>High</option>
                <option value="Urgent" style={{ background: '#0F172A' }}>Urgent</option>
                <option value="Low" style={{ background: '#0F172A' }}>Low</option>
              </select>
            </div>
          </div>

          {/* Actions */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            paddingTop: '0.5rem',
            borderTop: '1px solid rgba(255, 255, 255, 0.06)'
          }}>
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              id="submit-create-request"
            >
              <Check size={16} />
              <span>Submit Request</span>
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
