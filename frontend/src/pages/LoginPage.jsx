// Author: Fatma Türkmen - Geliştirici Giriş Sayfası Bileşeni
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AuthPages.css';

function EyeIcon({ open }) {
  return open
    ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
    : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>;
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: '', password: '', remember: false });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
    if (errors[name]) setErrors(p => { const n = { ...p }; delete n[name]; return n; });
    setApiError('');
  };

  const validate = () => {
    const e = {};
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = 'Geçerli bir e-posta girin';
    if (!form.password) e.password = 'Şifre zorunludur';
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    setApiError('');
    try {
      await login(form.email.trim().toLowerCase(), form.password);
      navigate('/profil', { replace: true });
    } catch (err) {
      const msg = err.response?.data?.detail;
      setApiError(typeof msg === 'string' ? msg : 'E-posta veya şifre hatalı.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Sol dekor */}
      <div className="auth-deco animate-fade-in">
        <div className="auth-deco-inner">
          <div className="auth-logo">
            <div className="auth-logo-icon">🎓</div>
            <span>AdaptLearn</span>
          </div>
          <h2 className="auth-deco-title">Tekrar Hoş Geldin!</h2>
          <p className="auth-deco-sub">Öğrenme yolculuğuna kaldığın yerden devam et.</p>
          <div className="auth-deco-stats">
            {[
              { value: '12K+', label: 'Aktif Öğrenci' },
              { value: '95%',  label: 'Memnuniyet' },
              { value: '500+', label: 'Ders İçeriği' },
            ].map(s => (
              <div key={s.label} className="auth-deco-stat">
                <div className="auth-deco-stat-value">{s.value}</div>
                <div className="auth-deco-stat-label">{s.label}</div>
              </div>
            ))}
          </div>
          <div className="auth-deco-blob blob-1" />
          <div className="auth-deco-blob blob-2" />
        </div>
      </div>

      {/* Sağ – form */}
      <div className="auth-form-panel">
        <div className="auth-form-wrap animate-fade-up">
          <div className="text-center">
            <h1 className="auth-title">Giriş Yap</h1>
            <p className="auth-subtitle">Hesabına erişmek için bilgilerini gir</p>
          </div>

          {apiError && (
            <div className="alert alert-error mt-16" role="alert" aria-live="assertive">❌ {apiError}</div>
          )}

          <form onSubmit={handleSubmit} noValidate className="auth-form" aria-label="Giriş formu">
            {/* Email */}
            <div className="form-group">
              <label className="form-label" htmlFor="login-email">E-posta</label>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">✉️</span>
                <input
                  id="login-email" name="email" type="email" required
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="ornek@email.com"
                  value={form.email} onChange={handleChange}
                  autoComplete="email"
                  aria-describedby={errors.email ? 'err-login-email' : undefined}
                />
              </div>
              {errors.email && <span id="err-login-email" className="form-error" role="alert">⚠ {errors.email}</span>}
            </div>

            {/* Şifre */}
            <div className="form-group">
              <div className="flex-between">
                <label className="form-label" htmlFor="login-pw">Şifre</label>
                <Link to="/sifremi-unuttum" className="auth-forgot">Şifremi Unuttum</Link>
              </div>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">🔒</span>
                <input
                  id="login-pw" name="password"
                  type={showPw ? 'text' : 'password'} required
                  className={`form-input ${errors.password ? 'error' : ''}`}
                  placeholder="Şifrenizi girin"
                  value={form.password} onChange={handleChange}
                  autoComplete="current-password"
                />
                <button type="button" className="input-action" onClick={() => setShowPw(v => !v)}
                  aria-label={showPw ? 'Şifreyi gizle' : 'Şifreyi göster'}>
                  <EyeIcon open={showPw} />
                </button>
              </div>
              {errors.password && <span className="form-error" role="alert">⚠ {errors.password}</span>}
            </div>

            {/* Beni Hatırla */}
            <label className="remember-check">
              <input type="checkbox" name="remember" checked={form.remember} onChange={handleChange} />
              <span>Beni hatırla</span>
            </label>

            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} aria-busy={loading}>
              {loading ? <><div className="spinner" /><span>Giriş yapılıyor...</span></> : 'Giriş Yap'}
            </button>
          </form>

          <div className="divider"><span>veya</span></div>

          <p className="auth-switch">
            Hesabın yok mu? <Link to="/kayit">Üye Ol</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
