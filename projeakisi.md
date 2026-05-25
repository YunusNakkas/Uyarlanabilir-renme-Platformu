# Uyarlanabilir-renme-Platformu

Makine Öğrenmesi Tabanlı Veri Analiz ve Tahminleme Sistemi
Bu proje, belirli veri setleri üzerinden örüntüleri tanıyabilen ve geleceğe yönelik tahminlerde bulunabilen bir Öğrenilebilir Yazılım (Machine Learning) prototipidir. Yazılım mühendisliği prensipleri ile veri bilimi tekniklerini birleştirerek, ham veriden anlamlı sonuçlar çıkarmayı hedefler.

🧠 Projenin Amacı
Proje, verilerin ön işlemeden geçirilmesi, model eğitimi ve sonuçların değerlendirilmesi süreçlerini kapsar. Temel odak noktası, modelin doğruluk (accuracy) oranını optimize ederek, gerçek dünya senaryolarına en yakın çıktıları üretmektir.

🚀 Öne Çıkan Özellikler
Veri Ön İşleme (Data Preprocessing): Eksik verilerin tamamlanması, gürültülü verilerin temizlenmesi ve normalizasyon işlemleri.

Özellik Mühendisliği (Feature Engineering): Modelin başarısını artırmak için anlamlı özelliklerin seçimi ve dönüştürülmesi.

Model Eğitimi: Denetimli (Supervised) veya Denetimsiz (Unsupervised) öğrenme algoritmalarının uygulanması.

Performans Analizi: Karışıklık matrisi (Confusion Matrix), F1-Skoru ve MSE gibi metriklerle modelin başarısının ölçülmesi.

Tahminleme Arayüzü: Kullanıcının yeni veri girişleri yaparak modelden sonuç alabilmesi.

🛠 Kullanılan Teknolojiler ve Kütüphaneler
Dil: Python

Veri Analizi: Pandas, NumPy

Görselleştirme: Matplotlib, Seaborn

Makine Öğrenmesi: Scikit-learn / TensorFlow / PyTorch (Hangisini kullandıysan)

Geliştirme Ortamı: Jupyter Notebook / Cursor / VS Code

Fatma TÜRKMEN 
Proje Analizi ve Kapsam Belirleme: Uyarlanabilir Öğrenme Platformu
Bu döküman, "Uyarlanabilir Öğrenme Platformu" projesinin hedeflerini, kullanıcı gereksinimlerini ve teknik sınırlarını belirlemek amacıyla hazırlanmıştır.

1. Proje Özeti
Platform, öğrencilerin öğrenme stillerine ve hızlarına uyum sağlayan, yapay zeka destekli kişiselleştirilmiş bir deneyim sunmayı amaçlar. Makine öğrenimi algoritmaları kullanarak öğrenci performansını analiz eder ve içeriği bu verilere göre dinamik olarak günceller.

2. Kullanıcı Rolleri (User Personas)
Öğrenci: İçeriklere erişen, testleri çözen ve kişiselleştirilmiş öğrenme yolunu takip eden ana kullanıcı.
Eğitmen: Eğitim materyalleri (video, PDF, test) yükleyen ve öğrenci gelişimini takip eden kullanıcı.
Yönetici (Admin): Platformun genel işleyişini, kullanıcı yetkilerini ve sistem ayarlarını yöneten yetkili.
3. Fonksiyonel Gereksinimler
Görsellerde belirtilen teslim edilecek ana başlıkların detaylandırılması:

3.1. Kullanıcı Kayıt ve Profil Yönetimi
E-posta ve şifre ile güvenli giriş/kayıt (JWT tabanlı).
Profil bilgilerinin (ad, ilgi alanları, öğrenme hedefleri) güncellenmesi.
Öğrenme geçmişi ve kazanılan rozetlerin görüntülenmesi.
3.2. İçerik Oluşturma ve Yönetim Sistemi (CMS)
Eğitmenler için kurs ve modül oluşturma arayüzü.
Farklı medya türlerinin (Video, Metin, Quiz) desteklenmesi.
İçeriklerin zorluk seviyelerine göre etiketlenmesi.
3.3. Öğrenme Analitiği ve Raporlama
Öğrencinin modül tamamlama oranlarının takibi.
Quiz başarı grafiklerinin görselleştirilmesi.
Eğitmenler için sınıf bazlı genel başarı raporları.
3.4. Kişiselleştirilmiş Öğrenme Yolları (Yapay Zeka)
Öğrencinin yanlış cevapladığı konularda ek materyal önerisi sunulması.
Öğrenme hızına göre bir sonraki içeriğin otomatik belirlenmesi.
Teknik: Scikit-learn kullanılarak öğrenci verilerinden model eğitimi yapılması.
3.5. Mobil Uyumlu Arayüz (Responsive Design)
React tabanlı, tüm ekran boyutlarında (Mobil, Tablet, Desktop) sorunsuz çalışan arayüz.
Kullanıcı dostu navigasyon ve etkileşimli elemanlar.
4. Teknik Kapsam ve Teknoloji Yığını
Frontend: React (State yönetimi için Context API veya Redux).
Backend: Node.js & Express.js.
Veritabanı: MongoDB (NoSQL yapısı sayesinde esnek veri depolama).
Yapay Zeka Modülü: Python (Scikit-learn).
Not: Node.js ile Python arasında child_process veya bir mikroservis mimarisi ile iletişim kurulacaktır.
5. Kapsam ve Sınırlar
Dahil Olanlar: İlk aşamada 5 ana teslimat kalemi.
Dahil Olmayanlar (V1): Canlı yayın desteği, ücretli kurs entegrasyonu (Ödeme sistemleri), sosyal topluluk forumları.
Doğrulama Planı
Kullanıcı Testleri: Öğrencilerin kişiselleştirilmiş önerileri faydalı bulup bulmadığının ölçülmesi.
Teknik Testler: AI modelinin doğruluk oranının (Accuracy) belirli bir eşiğin üzerinde olması.
Performans: Mobil cihazlarda sayfa yüklenme hızının optimize edilmesi.


