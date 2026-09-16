import React from 'react';
import { Bell, RefreshCw, Server, User as UserIcon, LogOut, ShieldCheck } from 'lucide-react';
import type { AuthUser } from '../../types/dashboard';

interface HeaderProps {
  lastUpdated: string;
  isAutoRefreshing: boolean;
  onRefresh: () => void;
  currentUser?: AuthUser | null;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  lastUpdated,
  isAutoRefreshing,
  onRefresh,
  currentUser,
  onLogout,
}) => {
  return (
    <header className="glass-panel" style={{ padding: '0.9rem 1.5rem', marginBottom: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        
        {/* Brand & Page Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(2, 132, 199, 0.4)',
            border: '1px solid rgba(255, 255, 255, 0.15)'
          }}>
            <Server size={22} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#F8FAFC' }}>
                Dashboard
              </h1>
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                padding: '0.15rem 0.5rem',
                borderRadius: '4px',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38BDF8',
                border: '1px solid rgba(56, 189, 248, 0.3)'
              }}>
                Layout 2 • Production
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#94A3B8', marginTop: '2px' }}>
              Dynamic Adaptive Load Ingestion System • VTNet Radio Operations
            </p>
          </div>
        </div>

        {/* Real-time Status and User Profile (Matching layout2.md: "Dashboard ... User") */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          
          {/* Telemetry Heartbeat */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.75rem',
            background: 'rgba(255, 255, 255, 0.04)',
            borderRadius: '9999px',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            fontSize: '0.75rem',
            color: '#94A3B8'
          }}>
            <span className={`pulse-dot ${isAutoRefreshing ? 'green' : 'amber'}`}></span>
            <span>Sync: <strong className="mono-data" style={{ color: '#F8FAFC' }}>{lastUpdated}</strong></span>
            <button
              onClick={onRefresh}
              aria-label="Refresh telemetry data"
              title="Manual refresh"
              style={{ display: 'flex', alignItems: 'center', color: '#94A3B8', marginLeft: '4px', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              <RefreshCw size={12} className={isAutoRefreshing ? 'spin-slow' : ''} />
            </button>
          </div>

          {/* Quick Notification Bell */}
          <button
            aria-label="System notifications"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              color: '#94A3B8',
              position: 'relative',
              cursor: 'pointer'
            }}
          >
            <Bell size={16} />
            <span style={{
              position: 'absolute',
              top: '6px',
              right: '6px',
              width: '6px',
              height: '6px',
              background: '#38BDF8',
              borderRadius: '50%'
            }} />
          </button>

          {/* User Profile matching layout2.md ("User") */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.35rem 0.75rem 0.35rem 0.4rem',
            borderRadius: '10px',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <div style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #38BDF8 0%, #0284C7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
              fontWeight: 700,
              fontSize: '0.85rem',
              boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)'
            }}>
              <UserIcon size={16} />
            </div>
            <div style={{ textAlign: 'left', lineHeight: '1.2' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#F8FAFC', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <span>{currentUser?.username || 'User'}</span>
                <ShieldCheck size={13} color="#10B981" />
              </div>
              <div style={{ fontSize: '0.7rem', color: '#38BDF8', fontWeight: 500 }}>
                {currentUser?.role || 'Radio Frequency Engineer'}
              </div>
            </div>

            {/* Logout button */}
            {onLogout && (
              <button
                onClick={onLogout}
                title="Đăng xuất khỏi hệ thống"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0.4rem',
                  marginLeft: '0.5rem',
                  borderRadius: '6px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  color: '#F87171',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
                  e.currentTarget.style.color = '#FCA5A5';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                  e.currentTarget.style.color = '#F87171';
                }}
              >
                <LogOut size={14} />
              </button>
            )}
          </div>

        </div>

      </div>
    </header>
  );
};
