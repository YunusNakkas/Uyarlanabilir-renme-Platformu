# 🗄️ Veritabanı Entegrasyonu ve Optimizasyonu

**Sorumlu:** Melike Keke 
**Görev:** Veritabanı Entegrasyonu ve Optimizasyonu  
**Teknoloji:** MongoDB + Mongoose (Node.js)

---

## 📁 Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `db.js` | MongoDB bağlantı kurulumu |
| `queries.js` | Şemalar, indeksler ve optimize sorgular |

---

## 🔧 Kurulum

Projeye `mongoose` paketini ekle:

```bash
npm install mongoose
```

Bağlantıyı uygulamanın başında çağır:

```js
const connectDB = require('./database/db');
connectDB();
```

---

## 🗂️ Koleksiyonlar

### 1. `users` — Kullanıcılar
- `name`, `email`, `role` (student/teacher)
- `learningStyle` (visual/auditory/reading)

### 2. `contents` — İçerikler
- `title`, `type` (text/video/quiz)
- `difficultyLevel` (1-5 arası zorluk)

### 3. `performances` — Öğrenci Performansları
- `completionRate` (tamamlama yüzdesi)
- `quizScore` (sınav puanı)
- `timeSpent` (harcanan süre)

---

## ⚡ Optimizasyon Stratejileri

- **İndeksleme** → Sık kullanılan sorgular hızlandırıldı
- `.lean()` kullanımı → Gereksiz yük kaldırıldı
- `.select()` kullanımı → Sadece gerekli alanlar çekildi
- `aggregate()` → Hesaplamalar veritabanı tarafında yapıldı

---

## 📊 Hazır Fonksiyonlar

| Fonksiyon | Açıklama |
|-----------|----------|
| `getStudentPerformance` | Öğrencinin performans geçmişi |
| `getAverageScore` | Ortalama puan ve istatistikler |
| `recommendContent` | Kişiselleştirilmiş içerik önerisi |
| `getPlatformStats` | Platform geneli istatistikler |

---

## 🤖 Kişiselleştirme Mantığı

| Ortalama Puan | Önerilen Zorluk |
|---------------|-----------------|
| 0 - 49 | Kolay (1-2) — Tekrar listesi |
| 50 - 74 | Orta (3) — Normal ilerleme |
| 75 - 100 | Zor (4-5) — İleri seviye |
