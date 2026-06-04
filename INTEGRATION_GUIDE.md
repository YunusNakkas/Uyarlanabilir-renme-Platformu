# 🔌 API Entegrasyon Rehberi

Bu doküman, üçüncü taraf eğitim araçlarının platforma entegre edilme sürecini kapsar.

## 1. Hedef API'lar
* **Zoom API:** Canlı derslerin platform üzerinden başlatılması.
* **Quizlet API:** Hazır çalışma setlerinin sisteme çekilmesi.

## 2. Entegrasyon Adımları
1. API anahtarlarının (Client ID, Secret) `.env` dosyasında güvenli şekilde saklanması.
2. Webhook yapılandırması ile araçlardan gelen verilerin (örn: ders bitişi) anlık takibi.
3. OAuth2 protokolü ile kullanıcı yetkilendirmesi.

## 3. Doğrulama (Testing)
Entegrasyonun çalıştığını doğrulamak için Postman üzerinden uç nokta (endpoint) testleri gerçekleştirilecektir.