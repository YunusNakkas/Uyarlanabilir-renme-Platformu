import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AuthPages.css';

/* ─── Yardımcılar ─── */
function getStrength(pw) {
  let score = 0;
  if (pw.length >= 8)  score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score; // 0-4
}
const strengthLabels = ['', 'Zayıf', 'Orta', 'İyi', 'Güçlü'];
const strengthClasses = ['', 'weak', 'fair', 'good', 'strong'];

function EyeIcon({ open }) {
  return open
    ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
    : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>;
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    ad: '', soyad: '', email: '', password: '', confirmPassword: '',
    role: 'ogrenci', kvkk: false,
  });
  const [errors, setErrors] = useState({});
  const [showPw, setShowPw] = useState(false);
  const [showCpw, setShowCpw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [apiError, setApiError] = useState('');

  const strength = getStrength(form.password);

  const validate = () => {
    const e = {};
    if (!form.ad.trim())    e.ad = 'Ad zorunludur';
    if (!form.soyad.trim()) e.soyad = 'Soyad zorunludur';
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = 'Geçerli bir e-posta girin';
    if (form.password.length < 8) e.password = 'En az 8 karakter olmalı';
    if (form.password !== form.confirmPassword) e.confirmPassword = 'Şifreler eşleşmiyor';
    if (!form.kvkk) e.kvkk = 'KVKK onayı zorunludur';
    return e;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
    if (errors[name]) setErrors(prev => { const n = { ...prev }; delete n[name]; return n; });
    setApiError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    setApiError('');
    try {
      await register({
        ad: form.ad.trim(),
        soyad: form.soyad.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        role: form.role,
      });
      setSuccess('Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz...');
      setTimeout(() => navigate('/giris'), 2000);
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Kayıt sırasında bir hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Sol panel – dekor */}
      <div className="auth-deco animate-fade-in">
        <div className="auth-deco-inner">
          <div className="auth-logo">
            <div className="auth-logo-icon">🎓</div>
            <span>AdaptLearn</span>
          </div>
          <h2 className="auth-deco-title">Uyarlanabilir Öğrenme Platformu</h2>
          <p className="auth-deco-sub">Yapay zeka destekli, kişiselleştirilmiş öğrenme deneyimi.</p>
          <div className="auth-deco-features">
            {['🤖 AI destekli içerik', '📊 Kişisel performans analizi', '🏆 Gamification sistemi', '📱 Mobil uyumlu arayüz'].map(f => (
              <div key={f} className="auth-deco-feature">{f}</div>
            ))}
          </div>
          <div className="auth-deco-blob blob-1" />
          <div className="auth-deco-blob blob-2" />
        </div>
      </div>

      {/* Sağ panel – form */}
      <div className="auth-form-panel">
        <div className="auth-form-wrap animate-fade-up">
          <div className="text-center">
            <h1 className="auth-title">Hesap Oluştur</h1>
            <p className="auth-subtitle">Ücretsiz üye ol, öğrenmeye başla</p>
          </div>

          {success && <div className="alert alert-success mt-16" role="status" aria-live="polite">✅ {success}</div>}
          {apiError && <div className="alert alert-error mt-16" role="alert" aria-live="assertive">❌ {apiError}</div>}

          <form onSubmit={handleSubmit} noValidate className="auth-form" aria-label="Kayıt formu">
            {/* Ad – Soyad */}
            <div className="auth-row">
              <div className="form-group">
                <label className="form-label" htmlFor="reg-ad">Ad</label>
                <div className="input-wrapper">
                  <span className="input-icon" aria-hidden="true">👤</span>
                  <input
                    id="reg-ad" name="ad" type="text" required
                    className={`form-input ${errors.ad ? 'error' : ''}`}
                    placeholder="Adınız"
                    value={form.ad} onChange={handleChange}
                    autoComplete="given-name"
                    aria-describedby={errors.ad ? 'err-ad' : undefined}
                  />
                </div>
                {errors.ad && <span id="err-ad" className="form-error" role="alert">⚠ {errors.ad}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="reg-soyad">Soyad</label>
                <div className="input-wrapper">
                  <span className="input-icon" aria-hidden="true">👤</span>
                  <input
                    id="reg-soyad" name="soyad" type="text" required
                    className={`form-input ${errors.soyad ? 'error' : ''}`}
                    placeholder="Soyadınız"
                    value={form.soyad} onChange={handleChange}
                    autoComplete="family-name"
                    aria-describedby={errors.soyad ? 'err-soyad' : undefined}
                  />
                </div>
                {errors.soyad && <span id="err-soyad" className="form-error" role="alert">⚠ {errors.soyad}</span>}
              </div>
            </div>

            {/* Email */}
            <div className="form-group">
              <label className="form-label" htmlFor="reg-email">E-posta</label>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">✉️</span>
                <input
                  id="reg-email" name="email" type="email" required
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="ornek@email.com"
                  value={form.email} onChange={handleChange}
                  autoComplete="email"
                  aria-describedby={errors.email ? 'err-email' : undefined}
                />
              </div>
              {errors.email && <span id="err-email" className="form-error" role="alert">⚠ {errors.email}</span>}
            </div>

            {/* Şifre */}
            <div className="form-group">
              <label className="form-label" htmlFor="reg-password">Şifre</label>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">🔒</span>
                <input
                  id="reg-password" name="password"
                  type={showPw ? 'text' : 'password'}
                  required
                  className={`form-input ${errors.password ? 'error' : ''}`}
                  placeholder="En az 8 karakter"
                  value={form.password} onChange={handleChange}
                  autoComplete="new-password"
                  aria-describedby="pw-strength"
                />
                <button type="button" className="input-action" onClick={() => setShowPw(v => !v)}
                  aria-label={showPw ? 'Şifreyi gizle' : 'Şifreyi göster'}>
                  <EyeIcon open={showPw} />
                </button>
              </div>
              {errors.password && <span className="form-error" role="alert">⚠ {errors.password}</span>}
              {form.password && (
                <div id="pw-strength" aria-label={`Şifre gücü: ${strengthLabels[strength]}`}>
                  <div className="strength-bars" role="presentation">
                    {[1,2,3,4].map(i => (
                      <div key={i} className={`strength-bar ${i <= strength ? strengthClasses[strength] : ''}`} />
                    ))}
                  </div>
                  <span className={`form-hint strength-label-${strengthClasses[strength]}`} style={{ fontSize: '0.78rem' }}>
                    Şifre gücü: <b>{strengthLabels[strength]}</b>
                  </span>
                </div>
              )}
            </div>

            {/* Şifre onay */}
            <div className="form-group">
              <label className="form-label" htmlFor="reg-cpw">Şifre Tekrar</label>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">🔒</span>
                <input
                  id="reg-cpw" name="confirmPassword"
                  type={showCpw ? 'text' : 'password'}
                  required
                  className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
                  placeholder="Şifrenizi tekrar girin"
                  value={form.confirmPassword} onChange={handleChange}
                  autoComplete="new-password"
                />
                <button type="button" className="input-action" onClick={() => setShowCpw(v => !v)}
                  aria-label={showCpw ? 'Şifreyi gizle' : 'Şifreyi göster'}>
                  <EyeIcon open={showCpw} />
                </button>
              </div>
              {errors.confirmPassword && <span className="form-error" role="alert">⚠ {errors.confirmPassword}</span>}
            </div>

            {/* Rol seçimi */}
            <div className="form-group">
              <label className="form-label" htmlFor="reg-role">Kullanıcı Rolü</label>
              <div className="role-cards" role="radiogroup" aria-label="Kullanıcı rolü seçimi">
                {[
                  { v: 'ogrenci', icon: '🎓', label: 'Öğrenci' },
                  { v: 'ogretmen', icon: '📚', label: 'Öğretmen' },
                ].map(({ v, icon, label }) => (
                  <label key={v} className={`role-card ${form.role === v ? 'selected' : ''}`}>
                    <input type="radio" name="role" value={v}
                      checked={form.role === v} onChange={handleChange}
                      className="sr-only" />
                    <span className="role-icon" aria-hidden="true">{icon}</span>
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* KVKK */}
            <label className={`kvkk-check ${errors.kvkk ? 'error' : ''}`}>
              <input type="checkbox" name="kvkk" checked={form.kvkk} onChange={handleChange}
                aria-describedby={errors.kvkk ? 'err-kvkk' : undefined} />
              <span>
                <Link to="/kvkk" target="_blank" rel="noopener noreferrer">KVKK Aydınlatma Metni</Link>'ni
                ve <Link to="/gizlilik" target="_blank" rel="noopener noreferrer">Gizlilik Politikası</Link>'nı
                okudum, kabul ediyorum.
              </span>
            </label>
            {errors.kvkk && <span id="err-kvkk" className="form-error" role="alert">⚠ {errors.kvkk}</span>}

            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}
              aria-busy={loading}>
              {loading ? <><div className="spinner" /><span>Kaydediliyor...</span></> : 'Üye Ol'}
            </button>
          </form>

          <div className="divider"><span>veya</span></div>

          <p className="auth-switch">
            Zaten hesabın var mı? <Link to="/giris">Giriş Yap</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
