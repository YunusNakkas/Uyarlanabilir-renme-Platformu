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
1. Sunucuyu başlatın: `npm start`
2. ML servisini kontrol edin: `python backend/ml_service.py`