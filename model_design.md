#  Makine Öğrenimi ve Analitik Sistem Tasarımı

Bu doküman, **Uyarlanabilir Öğrenme Platformu** projesinin zeka modülü, veri analitiği ve sistem iyileştirme süreçlerini detaylandırmaktadır.

## 1. Algoritma Tasarımı ve Veri Özellikleri (Features)
Öğrenci performansını analiz etmek ve kişiselleştirilmiş öğrenme yolları oluşturmak için **Scikit-learn** kütüphanesi kullanılacaktır. 

### A. Kullanılacak Veri Özellikleri (Input Features)
Modelin eğitimi ve tahmini için şu veriler kullanılacaktır:
*   **Tamamlama Oranı (completionRate):** İçeriğin ne kadarının tüketildiği.
*   **Sınav Puanı (quizScore):** Ders sonu testlerinden alınan başarı notu.
*   **Zorluk Seviyesi (difficultyLevel):** İçeriğin 1-5 arası zorluk derecesi.
*   **Öğrenme Stili (learningStyle):** Görsel, işitsel veya okuma odaklı tercihler.

### B. Algoritma Seçimi
*   **Sınıflandırma (Decision Tree):** Öğrencinin seviyesini ayırmak için.
*   **Kişiselleştirme Mantığı:** Düşük puanlı öğrenciye "Tekrar Listesi", yüksek puanlıya "İleri Seviye" içerik önerilir.

## 2. Analitik Raporlama Paneli
Kullanıcı davranışlarını izlemek amacıyla hem eğitmenler hem de öğrenciler için bir panel tasarlanmıştır.
*   **İzlenecek Metrikler:** Toplam ders saati, konu bazlı başarı yüzdeleri.

## 3. API Entegrasyonu
Platformun eğitim kapsamını genişletmek amacıyla üçüncü taraf araçlarla (Örn: Gemini/Grok API) entegrasyon altyapısı kurulmuştur.
