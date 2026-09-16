import React, { useState } from 'react';
import { Radio, Lock, User, Eye, EyeOff, ShieldCheck, AlertCircle, ArrowRight, Loader2, Sparkles } from 'lucide-react';
import { apiService } from '../../services/api';
import type { AuthUser } from '../../types/dashboard';

interface LoginPageProps {
  onLoginSuccess: (user: AuthUser) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('huydq52');
  const [password, setPassword] = useState('Huy9191@');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMsg('Vui lòng nhập đầy đủ tên tài khoản và mật khẩu');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      await apiService.login(username.trim(), password);
      // Fetch authenticated user profile
      const user = await apiService.getMe();
      onLoginSuccess(user);
    } catch (err: any) {
      console.error('Login error:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMsg(detail);
      } else if (Array.isArray(detail)) {
        setErrorMsg(detail.map((d: any) => d.msg || d.message).join(', '));
      } else {
        setErrorMsg('Đăng nhập thất bại. Vui lòng kiểm tra tài khoản hoặc kết nối server.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFillHuydq = () => {
    setUsername('huydq52');
    setPassword('Huy9191@');
    setErrorMsg(null);
  };

  return (
    <div className="login-page-container">
      {/* Dynamic Glowing Accents */}
      <div className="login-glow-1" />
      <div className="login-glow-2" />

      {/* Login Card */}
      <div className="login-card">
        
        {/* Brand Header */}
        <div className="login-header">
          <div className="login-brand-icon">
            <Radio size={28} color="#FFFFFF" />
          </div>
          <h1 className="login-brand-title">
            VTNet Radio Ops
          </h1>
          <p className="login-brand-subtitle">
            Telecom RF Anomaly & Data Ingestion
          </p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="login-error-alert animate-fadeIn">
            <AlertCircle size={16} color="#F87171" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>{errorMsg}</div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div className="login-field">
            <label className="login-field-label">
              Tên tài khoản (Username)
            </label>
            <div className="login-input-wrapper">
              <span className="login-input-icon">
                <User size={16} />
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Ví dụ: huydq52"
                className="login-input"
                required
              />
            </div>
          </div>

          <div className="login-field">
            <label className="login-field-label">
              Mật khẩu (Password)
            </label>
            <div className="login-input-wrapper">
              <span className="login-input-icon">
                <Lock size={16} />
              </span>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Nhập mật khẩu"
                className="login-input"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="login-toggle-pw"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Quick Preset Chip */}
          <button
            type="button"
            onClick={handleFillHuydq}
            className="login-quick-chip"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sparkles size={14} color="#38BDF8" />
              <span>Điền nhanh: <strong style={{ color: '#F8FAFC' }}>huydq52</strong></span>
            </div>
            <span style={{
              fontSize: '0.68rem',
              padding: '0.15rem 0.45rem',
              borderRadius: '4px',
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38BDF8',
              fontWeight: 600
            }}>
              RF Engineer
            </span>
          </button>

          <button
            type="submit"
            disabled={isLoading}
            className="login-submit-btn"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="spin-slow" />
                <span>Đang xác thực Backend TimescaleDB...</span>
              </>
            ) : (
              <>
                <span>Đăng nhập hệ thống</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div className="login-footer-info">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <ShieldCheck size={14} color="#10B981" />
            <span>FastAPI • TimescaleDB</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#10B981' }}>
            <span className="pulse-dot green" style={{ width: '6px', height: '6px' }}></span>
            <span>Port 8000 Online</span>
          </div>
        </div>

      </div>
    </div>
  );
};
