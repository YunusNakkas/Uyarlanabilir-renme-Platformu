import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../api/auth';
import './AuthPages.css';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setError('Geçerli bir e-posta adresi girin.'); return;
    }
    setLoading(true); setError('');
    try {
      await authApi.forgotPassword(email.trim().toLowerCase());
      setSuccess('Şifre sıfırlama bağlantısı e-posta adresinize gönderildi. Lütfen gelen kutunuzu kontrol edin.');
    } catch (err) {
      setError(err.response?.data?.detail || 'İşlem sırasında bir hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form-panel" style={{ minHeight: '100vh' }}>
      <div className="auth-form-wrap animate-scale-in" style={{ maxWidth: 420 }}>
        <div className="text-center">
          <div style={{ fontSize: '3rem', marginBottom: 12 }}>🔑</div>
          <h1 className="auth-title">Şifremi Unuttum</h1>
          <p className="auth-subtitle">
            E-posta adresinizi girin, sıfırlama bağlantısı gönderelim.
          </p>
        </div>

        {success && <div className="alert alert-success mt-16" role="status" aria-live="polite">✅ {success}</div>}
        {error   && <div className="alert alert-error mt-16"   role="alert"  aria-live="assertive">❌ {error}</div>}

        {!success && (
          <form onSubmit={handleSubmit} noValidate className="auth-form" aria-label="Şifre sıfırlama formu">
            <div className="form-group">
              <label className="form-label" htmlFor="forgot-email">E-posta Adresi</label>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">✉️</span>
                <input id="forgot-email" name="email" type="email" required
                  className="form-input"
                  placeholder="ornek@email.com"
                  value={email} onChange={e => { setEmail(e.target.value); setError(''); }}
                  autoComplete="email" />
              </div>
            </div>
            <button type="submit" className="btn btn-primary btn-full btn-lg"
              disabled={loading} aria-busy={loading}>
              {loading ? <><div className="spinner" /><span>Gönderiliyor...</span></> : '📨 Bağlantı Gönder'}
            </button>
          </form>
        )}

        <p className="auth-switch">
          <Link to="/giris">← Giriş sayfasına dön</Link>
        </p>
      </div>
    </div>
  );
}
