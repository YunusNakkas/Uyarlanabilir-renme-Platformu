# 🧠 Makine Öğrenmesi Algoritma Tasarımı

Bu doküman, kişiselleştirilmiş öğrenme yolları oluşturmak için tasarlanan algoritma seçim sürecini içerir.

## 1. Belirlenen Veri Özellikleri (Features)
Modelin eğitimi için şu veri özellikleri kullanılacaktır:
* **Akademik Veriler:** Önceki sınav notları, ödev tamamlama oranları.
* **Kullanıcı Davranışları:** Video izleme süresi, platformda geçirilen toplam vakit.
* **Etkileşim:** Forum katılımı, sorulan soru sayısı.

## 2. Değerlendirilen Algoritmalar (Scikit-learn)
* **K-Means Kümeleme:** Öğrencileri benzer başarı gruplarına ayırmak için.
* **Random Forest Sınıflandırma:** Öğrencinin "Başarılı/Risk Altında" durumunu tahmin etmek için.
* **Decision Trees:** Öğrenciye özel öğrenme rotası çizmek için.

## 3. Geri Bildirim ve Değerlendirme
Ekip geri bildirimlerine göre modelin doğruluk (accuracy) ve duyarlılık (recall) metrikleri optimize edilecektir.