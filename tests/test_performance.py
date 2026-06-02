"""
📊 BACKEND MODEL PERFORMANS TESTİ (F1 Macro)
===========================================
Bu script, backend'de kullanılan Random Forest modelinin (tavsiye_modeli_v4.joblib)
tahmin başarısını ölçmek ve belirlenen eşik değerinin (0.80) üzerinde olup olmadığını 
kontrol etmek için kullanılır.
"""

import os
import joblib# type: ignore
import pandas as pd # type: ignore
import numpy as np
from sklearn.model_selection import train_test_split# type: ignore
from sklearn.metrics import f1_score, classification_report, confusion_matrix

# Ayarlar
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "tavsiye_modeli_v4.joblib")
CSV_PATH = os.path.join(PROJECT_ROOT, "StudentsPerformance_Extended.csv")
FEATURE_COLS = ['math score', 'physical score', 'chemical score', 'study_hours', 'sleep_hours']
F1_THRESHOLD = 0.80

def run_performance_test():
    print("\n🔍 Backend Model Performans Testi Başlatılıyor...")
    
    # 1. Model ve Veri Yükleme
    if not os.path.exists(MODEL_PATH):
        print(f"❌ HATA: Model dosyası bulunamadı: {MODEL_PATH}")
        return False
        
    if not os.path.exists(CSV_PATH):
        print(f"❌ HATA: Veri seti bulunamadı: {CSV_PATH}")
        return False

    try:
        model_data = joblib.load(MODEL_PATH)
        pipeline = model_data["pipeline"]
        df = pd.read_csv(CSV_PATH).dropna()
    except Exception as e:
        print(f"❌ HATA: Dosyalar yüklenirken sorun oluştu: {e}")
        return False

    # 2. Test Setini Hazırlama (Eğitim setiyle aynı mantıkta etiketleme)
    ortalama = df[["math score", "physical score", "chemical score"]].mean(axis=1)
    y = pd.qcut(ortalama, q=5, labels=False, duplicates="drop").astype(int)
    X = df[FEATURE_COLS]

    # Modelin görmediği bir test seti üzerinde değerlendirme yapmak için (%20 ayrım)
    # Not: Model zaten tüm veri üzerinde eğitilmiş olabilir, ancak bu test 
    # modelin genelleme yeteneğini veya mevcut durumdaki başarısını ölçer.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 3. Tahmin ve Metrik Hesaplama
    y_pred = pipeline.predict(X_test)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
    
    # 4. Sonuçları Yazdırma
    print("\n" + "="*60)
    print(f"🎯 PERFORMANS SONUÇLARI")
    print("="*60)
    print(f"📊 F1 Skoru (Macro): %{f1_macro*100:.2f}")
    print(f"📈 Hedef Eşik Değeri: %{F1_THRESHOLD*100:.2f}")
    
    status = "✅ BAŞARILI" if f1_macro >= F1_THRESHOLD else "❌ BAŞARISIZ"
    print(f"🏁 Test Durumu: {status}")
    print("="*60)

    print("\n📋 SINIFLANDIRMA RAPORU:")
    labels = sorted(list(set(y_test)))
    target_names = [f"Seviye {i}" for i in labels]
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))

    if f1_macro < F1_THRESHOLD:
        print(f"⚠️ UYARI: Model performansı beklenen eşik değerinin ({F1_THRESHOLD}) altında!")
        return False
        
    print("✅ Model performansı kriterleri karşılıyor.")
    return True

if __name__ == "__main__":
    success = run_performance_test()
    exit(0 if success else 1)
