# Frontend – Kullanıcı Arayüzü (UI)

> **Geliştirici:** Fatma Türkmen  
> **Görev:** Kullanıcı kayıt ve profil yönetimi için React arayüzü  
> **Teknoloji:** React 18 + Vite + React Router + Axios

## Kurulum

```bash
cd frontend
npm install
npm run dev
```

Tarayıcıda `http://localhost:5173` adresine gidin.

## Sayfalar

| Sayfa | URL | Açıklama |
|-------|-----|----------|
| Giriş | `/giris` | E-posta + şifre ile giriş |
| Kayıt | `/kayit` | Hesap oluşturma formu |
| Şifre Sıfırlama | `/sifremi-unuttum` | E-posta ile sıfırlama isteği |
| Profil | `/profil` | Profil bilgileri, şifre değiştirme, hesap ayarları |

## Özellikler

- ✅ Gerçek zamanlı form doğrulama
- ✅ Şifre güç göstergesi
- ✅ Şifre göster/gizle butonu
- ✅ Rol seçimi (Öğrenci / Öğretmen)
- ✅ KVKK onayı
- ✅ Avatar yükleme
- ✅ Profil düzenleme
- ✅ Şifre değiştirme
- ✅ Hesap silme (onaylı)
- ✅ Mobil uyumlu (responsive) tasarım
- ✅ Erişilebilirlik (ARIA, semantik HTML, klavye navigasyonu)
- ✅ Dark mode glassmorphism tasarım
- ✅ JWT token yönetimi

## Çevre Değişkenleri

`.env` dosyası oluşturun:

```env
VITE_API_URL=http://localhost:8000
```

## Dosya Yapısı

```
frontend/
├── src/
│   ├── api/
│   │   └── auth.js          # API istekleri
│   ├── context/
│   │   └── AuthContext.jsx  # Global auth state
│   ├── components/
│   │   └── RouteGuard.jsx   # Rota koruyucuları
│   ├── pages/
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── ProfilePage.jsx
│   │   ├── ForgotPasswordPage.jsx
│   │   ├── AuthPages.css
│   │   └── ProfilePage.css
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
└── index.html
```
