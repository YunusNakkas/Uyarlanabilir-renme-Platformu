import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 1. Gerçek Değerler ve Algoritma Tahminleri (Örnek Veri Seti)
# 1: Başarılı/Öğrenme yolunu tamamladı, 0: Risk altında/Destek gerekli
y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1])
y_pred = np.array([1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1])

# 2. Metriklerin Hesaplaması (Görev 1 ve 3 İçin)
accuracy = accuracy_score(y_true, y_pred)
print("=== ÖĞRENCİ PERFORMANS MODEL SONUÇLARI ===")
print(f"Model Doğruluk Oranı (Accuracy): %{accuracy * 100:.2f}")
print("\nDetaylı Sınıflandırma Raporu:")
print(classification_report(y_true, y_pred, target_names=['Risk Altında', 'Başarılı']))

# 3. Basit Bir Performans Grafiği Oluşturma (Görev 3 - Analitik Panel)
metrics = ['Doğruluk (Accuracy)', 'Hedef Başarı Oranı']
values = [accuracy, 0.85]  # %85 bizim hedefimiz olsun

plt.bar(metrics, values, color=['blue', 'green'])
plt.ylabel('Oran')
plt.title('Platform ve Model Performans Analitiği')
plt.ylim(0, 1.0)
print("Analitik rapor grafiği simüle edildi. (evaluate_model_performance.png)")