# 📚 Uyarlanabilir Öğrenme Platformu — Dokümantasyon

---

## 1. 🎯 Proje Hakkında

Uyarlanabilir Öğrenme Platformu, öğrencilerin öğrenme hızlarına ve stillerine uyum sağlayan, kişiselleştirilmiş bir eğitim deneyimi sunan bir platformdur. Yapay zeka kullanarak öğrenci performansını analiz eder ve içerikleri buna göre uyarlar.

---

## 2. 🛠️ Kullanılan Teknolojiler

| Teknoloji | Kullanım Amacı |
|-----------|---------------|
| React | Kullanıcı arayüzü |
| Node.js | Backend API |
| MongoDB | Veritabanı |
| Scikit-learn | Makine öğrenimi |
| Mongoose | MongoDB bağlantısı |
| Jest | Otomatik testler |

---

## 3. 👥 Kullanım Kılavuzu

### Öğrenci Olarak
1. Platforma kayıt ol
2. Profilini oluştur, öğrenme stilini seç
3. Sana önerilen içerikleri tamamla
4. Sınavlara gir, puanını gör
5. Sistem sana göre içerik zorluğunu otomatik ayarlar

### Öğretmen Olarak
1. Platforma öğretmen olarak kayıt ol
2. İçerik oluştur (metin, video, sınav)
3. Öğrenci performanslarını takip et
4. Analitik panelden raporları incele

---

## 4. 🗄️ Veritabanı Yapısı

### Kullanıcılar (users)
- `name` — Ad Soyad
- `email` — E-posta (benzersiz)
- `role` — Rol (student/teacher)
- `learningStyle` — Öğrenme stili (visual/auditory/reading)

### İçerikler (contents)
- `title` — İçerik başlığı
- `type` — Tür (text/video/quiz)
- `difficultyLevel` — Zorluk (1-5)
- `subject` — Konu

### Performanslar (performances)
- `student` — Öğrenci referansı
- `content` — İçerik referansı
- `completionRate` — Tamamlama yüzdesi
- `quizScore` — Sınav puanı
- `timeSpent` — Harcanan süre

---

## 5. 🤖 Kişiselleştirme Sistemi

| Ortalama Puan | Önerilen Zorluk |
|---------------|-----------------|
| 0 - 49 | Kolay (1-2) — Tekrar listesi |
| 50 - 74 | Orta (3) — Normal ilerleme |
| 75 - 100 | Zor (4-5) — İleri seviye |

---

## 6. 🔒 Güvenlik Önlemleri

- NoSQL Injection koruması
- Bcrypt ile şifre hashleme
- JWT token kimlik doğrulama
- CORS yapılandırması
- Rate limiting (brute-force koruması)

---

## 7. 🧪 Testler

Platformda 8 otomatik test senaryosu bulunmaktadır:

- Kullanıcı kayıt/giriş testleri (4 test)
- İçerik yönetim testleri (2 test)
- Performans ve öneri testleri (2 test)

**Tüm testler başarıyla geçmektedir. ✅**
