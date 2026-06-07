# 🧠 Yapay Zeka Model Analiz Raporu

Bu rapor, öğrenci performansını tahmin eden modelin teknik detaylarını ve başarı metriklerini içerir.

## 1. Model Mimarisi
* **Algoritma:** Scikit-learn kütüphanesi kullanılarak eğitilen sınıflandırma modeli.
* **Kullanılan Özellikler (Features):** Çalışma saatleri, önceki sınav notları ve katılım oranları.

## 2. Performans Analizi
Modelin başarısını ölçmek için kullanılan temel metrikler:
* **F1-Skoru:** Modelin dengeli başarı oranı.
* **Isı Haritası (Heatmap):** Gerçek değerler ile tahmin edilen değerler arasındaki farkları görselleştirmek için `seaborn` kullanılarak hata matrisi oluşturulmuştur.

## 3. Görselleştirme Çıktısı
Daha önce eklenen `model_test_f1.py` betiği çalıştırıldığında, modelin hangi sınıfları (Örn: Geçti/Kaldı veya Not Seviyeleri) daha iyi ayırt edebildiği bir grafik olarak sunulmaktadır.