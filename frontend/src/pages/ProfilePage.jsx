// Author: Fatma Türkmen - Geliştirici Profil Sayfası Bileşeni
import { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { userApi } from '../api/auth';
import './ProfilePage.css';

const TABS = [
  { id: 'genel',    label: '👤 Profil Bilgileri' },
  { id: 'sifre',   label: '🔒 Şifre Değiştir' },
  { id: 'hesap',   label: '⚙️ Hesap Ayarları' },
];

function getInitials(ad, soyad) {
  return `${(ad?.[0] || '').toUpperCase()}${(soyad?.[0] || '').toUpperCase()}` || '?';
}

function getStrength(pw) {
  let s = 0;
  if (pw.length >= 8) s++;
  if (/[A-Z]/.test(pw)) s++;
  if (/[0-9]/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return s;
}
const strengthLabels = ['', 'Zayıf', 'Orta', 'İyi', 'Güçlü'];
const strengthClasses = ['', 'weak', 'fair', 'good', 'strong'];

function EyeIcon({ open }) {
  return open
    ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
    : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>;
}

/* ─── Alt Sekme: Genel Profil ─────────────────────────────── */
function TabGenel({ user, refreshUser }) {
  const [form, setForm] = useState({
    ad: user.ad || '',
    soyad: user.soyad || '',
    email: user.email || '',
    bio: user.bio || '',
    phone: user.phone || '',
    location: user.location || '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [apiError, setApiError] = useState('');
  const fileRef = useRef();
  const [avatarPreview, setAvatarPreview] = useState(user.avatar_url || null);
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarLoading, setAvatarLoading] = useState(false);

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    if (errors[e.target.name]) setErrors(p => { const n = { ...p }; delete n[e.target.name]; return n; });
    setSuccess(''); setApiError('');
  };

  const validate = () => {
    const e = {};
    if (!form.ad.trim())  e.ad = 'Ad zorunludur';
    if (!form.soyad.trim()) e.soyad = 'Soyad zorunludur';
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = 'Geçerli e-posta girin';
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    try {
      await userApi.updateProfile(form);
      await refreshUser();
      setSuccess('Profil bilgileriniz başarıyla güncellendi.');
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Güncelleme başarısız.');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { setApiError('Avatar 5 MB\'dan küçük olmalı.'); return; }
    if (!file.type.startsWith('image/')) { setApiError('Yalnızca resim dosyası yükleyebilirsiniz.'); return; }
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile) return;
    setAvatarLoading(true);
    try {
      await userApi.uploadAvatar(avatarFile);
      await refreshUser();
      setSuccess('Avatar güncellendi.');
      setAvatarFile(null);
    } catch (err) {
      setApiError('Avatar yüklenemedi.');
    } finally {
      setAvatarLoading(false);
    }
  };

  return (
    <div className="profile-tab-content animate-fade-up">
      {/* Avatar Bölümü */}
      <div className="avatar-section glass-card">
        <div className="avatar avatar-xl" onClick={() => fileRef.current?.click()} style={{ cursor: 'pointer' }}
          title="Fotoğrafı değiştirmek için tıkla" role="button" aria-label="Profil fotoğrafını değiştir"
          tabIndex={0} onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}>
          {avatarPreview
            ? <img src={avatarPreview} alt={`${form.ad} ${form.soyad}`} />
            : getInitials(form.ad, form.soyad)}
        </div>
        <div>
          <h3 className="avatar-name">{form.ad} {form.soyad}</h3>
          <span className="badge badge-primary">{user.role === 'ogretmen' ? '📚 Öğretmen' : '🎓 Öğrenci'}</span>
          <div className="avatar-actions">
            <input ref={fileRef} type="file" accept="image/*" className="sr-only"
              aria-label="Avatar seç" onChange={handleAvatarChange} />
            <button type="button" className="btn btn-secondary btn-sm"
              onClick={() => fileRef.current?.click()}>📷 Fotoğraf Seç</button>
            {avatarFile && (
              <button type="button" className="btn btn-primary btn-sm"
                onClick={handleAvatarUpload} disabled={avatarLoading} aria-busy={avatarLoading}>
                {avatarLoading ? <><div className="spinner" /><span>Yükleniyor...</span></> : '✅ Kaydet'}
              </button>
            )}
          </div>
          <p className="form-hint" style={{ marginTop: 6 }}>JPG, PNG veya GIF – max 5 MB</p>
        </div>
      </div>

      {success  && <div className="alert alert-success" role="status"  aria-live="polite">✅ {success}</div>}
      {apiError && <div className="alert alert-error"   role="alert"   aria-live="assertive">❌ {apiError}</div>}

      <form onSubmit={handleSubmit} noValidate className="profile-form" aria-label="Profil güncelleme formu">
        {/* Ad – Soyad */}
        <div className="profile-row">
          <div className="form-group">
            <label className="form-label" htmlFor="pf-ad">Ad</label>
            <input id="pf-ad" name="ad" type="text" className={`form-input ${errors.ad ? 'error' : ''}`}
              value={form.ad} onChange={handleChange} autoComplete="given-name"
              aria-describedby={errors.ad ? 'err-pf-ad' : undefined} />
            {errors.ad && <span id="err-pf-ad" className="form-error" role="alert">⚠ {errors.ad}</span>}
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="pf-soyad">Soyad</label>
            <input id="pf-soyad" name="soyad" type="text" className={`form-input ${errors.soyad ? 'error' : ''}`}
              value={form.soyad} onChange={handleChange} autoComplete="family-name"
              aria-describedby={errors.soyad ? 'err-pf-soyad' : undefined} />
            {errors.soyad && <span id="err-pf-soyad" className="form-error" role="alert">⚠ {errors.soyad}</span>}
          </div>
        </div>

        {/* Email */}
        <div className="form-group">
          <label className="form-label" htmlFor="pf-email">E-posta</label>
          <div className="input-wrapper">
            <span className="input-icon" aria-hidden="true">✉️</span>
            <input id="pf-email" name="email" type="email"
              className={`form-input ${errors.email ? 'error' : ''}`}
              value={form.email} onChange={handleChange} autoComplete="email"
              aria-describedby={errors.email ? 'err-pf-email' : undefined} />
          </div>
          {errors.email && <span id="err-pf-email" className="form-error" role="alert">⚠ {errors.email}</span>}
        </div>

        {/* Telefon */}
        <div className="form-group">
          <label className="form-label" htmlFor="pf-phone">Telefon <span className="text-muted">(opsiyonel)</span></label>
          <div className="input-wrapper">
            <span className="input-icon" aria-hidden="true">📞</span>
            <input id="pf-phone" name="phone" type="tel"
              className="form-input" value={form.phone} onChange={handleChange}
              placeholder="+90 5XX XXX XX XX" autoComplete="tel" />
          </div>
        </div>

        {/* Konum */}
        <div className="form-group">
          <label className="form-label" htmlFor="pf-loc">Şehir / Konum <span className="text-muted">(opsiyonel)</span></label>
          <div className="input-wrapper">
            <span className="input-icon" aria-hidden="true">📍</span>
            <input id="pf-loc" name="location" type="text"
              className="form-input" value={form.location} onChange={handleChange}
              placeholder="İstanbul, Türkiye" />
          </div>
        </div>

        {/* Hakkında */}
        <div className="form-group">
          <label className="form-label" htmlFor="pf-bio">Hakkımda <span className="text-muted">(opsiyonel)</span></label>
          <textarea id="pf-bio" name="bio" rows={4}
            className="form-input form-textarea"
            value={form.bio} onChange={handleChange}
            placeholder="Kendinizden kısaca bahsedin..." maxLength={500} />
          <span className="form-hint">{form.bio.length} / 500</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" className="btn btn-primary" disabled={loading} aria-busy={loading}>
            {loading ? <><div className="spinner" /><span>Kaydediliyor...</span></> : '💾 Değişiklikleri Kaydet'}
          </button>
        </div>
      </form>
    </div>
  );
}

/* ─── Alt Sekme: Şifre Değiştir ─────────────────────────── */
function TabSifre() {
  const [form, setForm] = useState({ current: '', newPw: '', confirm: '' });
  const [show, setShow] = useState({ current: false, newPw: false, confirm: false });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [apiError, setApiError] = useState('');

  const strength = getStrength(form.newPw);

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    if (errors[e.target.name]) setErrors(p => { const n = { ...p }; delete n[e.target.name]; return n; });
    setSuccess(''); setApiError('');
  };

  const toggle = (field) => setShow(s => ({ ...s, [field]: !s[field] }));

  const validate = () => {
    const e = {};
    if (!form.current) e.current = 'Mevcut şifrenizi girin';
    if (form.newPw.length < 8) e.newPw = 'En az 8 karakter olmalı';
    if (form.newPw === form.current) e.newPw = 'Yeni şifre mevcut şifreden farklı olmalı';
    if (form.newPw !== form.confirm) e.confirm = 'Şifreler eşleşmiyor';
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setLoading(true);
    try {
      await userApi.changePassword(form.current, form.newPw);
      setSuccess('Şifreniz başarıyla güncellendi.');
      setForm({ current: '', newPw: '', confirm: '' });
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Şifre güncellenemedi. Mevcut şifrenizi kontrol edin.');
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: 'current', label: 'Mevcut Şifre', placeholder: 'Mevcut şifreniz', autocomplete: 'current-password' },
    { key: 'newPw',   label: 'Yeni Şifre',    placeholder: 'En az 8 karakter', autocomplete: 'new-password' },
    { key: 'confirm', label: 'Yeni Şifre Tekrar', placeholder: 'Şifreyi tekrar girin', autocomplete: 'new-password' },
  ];

  return (
    <div className="profile-tab-content animate-fade-up">
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 className="section-title">🔒 Şifre Değiştir</h3>
        <p className="text-muted text-sm" style={{ marginBottom: 24 }}>
          Güvenliğiniz için güçlü bir şifre kullanmanızı öneririz.
        </p>

        {success  && <div className="alert alert-success mt-16" role="status" aria-live="polite">✅ {success}</div>}
        {apiError && <div className="alert alert-error mt-16"   role="alert"  aria-live="assertive">❌ {apiError}</div>}

        <form onSubmit={handleSubmit} noValidate className="profile-form" aria-label="Şifre değiştirme formu">
          {fields.map(({ key, label, placeholder, autocomplete }) => (
            <div className="form-group" key={key}>
              <label className="form-label" htmlFor={`pw-${key}`}>{label}</label>
              <div className="input-wrapper">
                <span className="input-icon" aria-hidden="true">🔒</span>
                <input id={`pw-${key}`} name={key}
                  type={show[key] ? 'text' : 'password'}
                  className={`form-input ${errors[key] ? 'error' : ''}`}
                  value={form[key]} onChange={handleChange}
                  placeholder={placeholder} autoComplete={autocomplete}
                  aria-describedby={errors[key] ? `err-pw-${key}` : undefined} />
                <button type="button" className="input-action" onClick={() => toggle(key)}
                  aria-label={show[key] ? 'Şifreyi gizle' : 'Şifreyi göster'}>
                  <EyeIcon open={show[key]} />
                </button>
              </div>
              {errors[key] && <span id={`err-pw-${key}`} className="form-error" role="alert">⚠ {errors[key]}</span>}
              {key === 'newPw' && form.newPw && (
                <>
                  <div className="strength-bars" role="presentation">
                    {[1,2,3,4].map(i => (
                      <div key={i} className={`strength-bar ${i <= strength ? strengthClasses[strength] : ''}`} />
                    ))}
                  </div>
                  <span className="form-hint">Güç: <b>{strengthLabels[strength]}</b></span>
                </>
              )}
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-primary" disabled={loading} aria-busy={loading}>
              {loading ? <><div className="spinner" /><span>Güncelleniyor...</span></> : '🔑 Şifreyi Güncelle'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ─── Alt Sekme: Hesap Ayarları ─────────────────────────── */
function TabHesap({ user, logout }) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteInput, setDeleteInput] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [apiError, setApiError] = useState('');

  const handleDelete = async () => {
    if (deleteInput !== 'HESABIMI SİL') return;
    setDeleting(true);
    try {
      await userApi.deleteAccount();
      logout();
    } catch {
      setApiError('Hesap silinemedi. Lütfen tekrar deneyin.');
      setDeleting(false);
    }
  };

  return (
    <div className="profile-tab-content animate-fade-up">
      {/* Hesap Bilgileri */}
      <div className="glass-card" style={{ padding: '24px', marginBottom: 16 }}>
        <h3 className="section-title">ℹ️ Hesap Bilgileri</h3>
        <div className="info-grid">
          <div className="info-item"><span className="info-label">Kullanıcı ID</span><span className="info-value">#{user.id}</span></div>
          <div className="info-item"><span className="info-label">Rol</span><span className="info-value">{user.role === 'ogretmen' ? 'Öğretmen' : 'Öğrenci'}</span></div>
          <div className="info-item"><span className="info-label">Kayıt Tarihi</span>
            <span className="info-value">{user.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : '—'}</span></div>
          <div className="info-item"><span className="info-label">Hesap Durumu</span>
            <span className="badge badge-success">✓ Aktif</span></div>
        </div>
      </div>

      {/* Tehlikeli Bölge */}
      <div className="glass-card danger-zone" style={{ padding: '24px' }}>
        <h3 className="section-title danger-title">⚠️ Tehlikeli Bölge</h3>
        <p className="text-muted text-sm" style={{ marginBottom: 16 }}>
          Bu işlemler geri alınamaz. Lütfen dikkatli olun.
        </p>

        {apiError && <div className="alert alert-error" role="alert">❌ {apiError}</div>}

        {!confirmDelete ? (
          <button type="button" className="btn btn-danger btn-sm"
            onClick={() => setConfirmDelete(true)}>🗑️ Hesabımı Sil</button>
        ) : (
          <div className="delete-confirm">
            <p className="text-sm" style={{ marginBottom: 12 }}>
              Devam etmek için <b style={{ color: '#f87171' }}>HESABIMI SİL</b> yazın:
            </p>
            <input type="text" className="form-input" placeholder="HESABIMI SİL"
              value={deleteInput} onChange={e => setDeleteInput(e.target.value)}
              aria-label="Hesap silme onayı" />
            <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
              <button type="button" className="btn btn-secondary btn-sm"
                onClick={() => { setConfirmDelete(false); setDeleteInput(''); }}>İptal</button>
              <button type="button" className="btn btn-danger btn-sm"
                disabled={deleteInput !== 'HESABIMI SİL' || deleting}
                onClick={handleDelete} aria-busy={deleting}>
                {deleting ? <><div className="spinner" /><span>Siliniyor...</span></> : 'Kalıcı Olarak Sil'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Ana Profil Sayfası ──────────────────────────────── */
export default function ProfilePage() {
  const { user, refreshUser, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('genel');

  if (!user) return null;

  return (
    <div className="profile-page">
      {/* Üst başlık */}
      <div className="profile-header animate-fade-up">
        <div className="profile-header-inner">
          <div className="avatar avatar-lg">
            {user.avatar_url
              ? <img src={user.avatar_url} alt={`${user.ad} ${user.soyad}`} />
              : getInitials(user.ad, user.soyad)}
          </div>
          <div>
            <h1 className="profile-hero-name">{user.ad} {user.soyad}</h1>
            <p className="profile-hero-email">{user.email}</p>
            <span className="badge badge-primary" style={{ marginTop: 6 }}>
              {user.role === 'ogretmen' ? '📚 Öğretmen' : '🎓 Öğrenci'}
            </span>
          </div>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={logout} id="logout-btn">
          🚪 Çıkış Yap
        </button>
      </div>

      {/* Tab navigasyonu */}
      <nav className="profile-tabs" role="tablist" aria-label="Profil sekmeleri">
        {TABS.map(tab => (
          <button key={tab.id} role="tab" id={`tab-${tab.id}`}
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            className={`profile-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Tab içerikleri */}
      <div className="profile-content">
        <div id={`panel-genel`} role="tabpanel" aria-labelledby="tab-genel"
          hidden={activeTab !== 'genel'}>
          {activeTab === 'genel' && <TabGenel user={user} refreshUser={refreshUser} />}
        </div>
        <div id={`panel-sifre`} role="tabpanel" aria-labelledby="tab-sifre"
          hidden={activeTab !== 'sifre'}>
          {activeTab === 'sifre' && <TabSifre />}
        </div>
        <div id={`panel-hesap`} role="tabpanel" aria-labelledby="tab-hesap"
          hidden={activeTab !== 'hesap'}>
          {activeTab === 'hesap' && <TabHesap user={user} logout={logout} />}
        </div>
      </div>
    </div>
  );
}
