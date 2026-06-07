# ⚙️ Teknik Spesifikasyonlar

Bu doküman, sistemin çalışma mantığını ve kullanılan veri yapısını detaylandırır.

## 1. Kullanıcı Akış Şeması
1. **Veri Toplama:** Kullanıcının platform üzerindeki tıklamaları ve test sonuçları anlık olarak yakalanır.
2. **İşleme:** Scikit-learn modeli (Random Forest), bu verileri kullanarak öğrenciyi başarı seviyesine göre sınıflandırır.
3. **Kişiselleştirme:** Sınıflandırma sonucuna göre API üzerinden kullanıcıya özel "Video" veya "Makale" içerikleri önerilir.

## 2. Veri Sözlüğü (Data Dictionary)
| Değişken Adı | Tip | Açıklama |
| :--- | :--- | :--- |
| `study_time` | float | Haftalık ortalama çalışma süresi (saat). |
| `quiz_score` | int | Son girilen testin başarı puanı (0-100). |
| `engagement_score`| float | Platformda geçirilen vakit/aktiflik oranı. |
| `target_path` | string | Algoritmanın önerdiği öğrenme yolu (Örn: "Takviye", "İleri Seviye"). |