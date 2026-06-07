# 🛠️ Geliştirme Ortamı Kurulum Rehberi

Bu proje Node.js, PostgreSQL ve Python Machine Learning kütüphanelerini temel alır.

## 1. Ön Gereksinimler
* **Node.js:** v18 veya üzeri.
* **Python:** 3.10 veya üzeri.
* **PostgreSQL:** v14 veya üzeri.

## 2. Veri Tabanı Yapılandırması (PostgreSQL)
1. PostgreSQL üzerinde `ogrenme_platformu` adında bir veritabanı oluşturun.
2. `.env` dosyasındaki `DATABASE_URL` kısmını kendi bilgilerinizle güncelleyin:
   `postgresql://kullanici_adi:sifre@localhost:5432/ogrenme_platformu`

## 3. Backend ve ML Kurulumu
Termimalde şu komutları sırayla çalıştırın:

# Node.js bağımlılıkları için
npm install

# Python kütüphaneleri için
pip install -r requirements.txt

## 4. Uygulamayı Başlatma

### Frontend (React Arayüzü)
```bash
cd frontend
npm install
npm run dev
```
Giriş için tarayıcınızdan `http://localhost:5173` adresini açabilirsiniz.

### Backend (FastAPI Sunucusu)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
API servislerini kontrol etmek ve interaktif dökümantasyonu incelemek için `http://localhost:8000/docs` adresini ziyaret edebilirsiniz.

2. ML servisini kontrol edin: `python backend/ml_service.py`