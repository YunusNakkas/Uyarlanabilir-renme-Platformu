"""import matplotlib.pyplot as plt
import seaborn as sns
🧪 F1 SKORU TEST SCRİPTİ (Mevcut V4 Modeli İçin)
=================================================
Çalıştığımız mevcut modeli (tavsiye_modeli_v4.joblib)
yükler ve test seti üzerindeki performansını test eder.
"""

import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report, confusion_matrix

def test_et():
    # 1. Ayarlar
    MODEL_PATH = "tavsiye_modeli_v4.joblib"
    CSV_PATH = "StudentsPerformance_Extended.csv"
    FEATURE_COLS = ['math score', 'physical score', 'chemical score', 'study_hours', 'sleep_hours']
    
    try:
        # Modeli yükle
        model_data = joblib.load(MODEL_PATH)
        pipe = model_data["pipeline"]
        cv_f1 = model_data.get("cv_f1_macro_mean", "Bilinmiyor")
    except FileNotFoundError:
        print(f"❌ Model dosyası ({MODEL_PATH}) bulunamadı!")
        print("Lütfen önce 'python students_performance_starter.py' yazarak modeli eğitin.")
        return

    # Veriyi yükle
    try:
        df = pd.read_csv(CSV_PATH).dropna()
    except FileNotFoundError:
        print(f"❌ Veri seti ({CSV_PATH}) bulunamadı!")
        return

    # 2. Gerçek Etiketi Oluştur
    ortalama = df[["math score", "physical score", "chemical score"]].mean(axis=1)
    y = pd.qcut(ortalama, q=5, labels=False, duplicates="drop").astype(int)
    
    X = df[FEATURE_COLS]

    # Test/Train Ayrımı
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("\n📂 Model Testi Başlıyor...")
    print(f"   Toplam Veri: {len(df)}")
    print(f"   Test Seti: {len(X_test)} (%\20)")
    
    if cv_f1 != "Bilinmiyor":
        print(f"   Modelin Kayıtlı Çapraz Doğrulama (CV) Skoru: %{cv_f1*100:.1f}")

    # 3. Test Seti Üzerinde Tahmin
    y_pred = pipe.predict(X_test)
    
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
    
    print("\n" + "="*60)
    print(f"🎯 TEST SETİ SONUÇLARI")
    print("="*60)
    print(f"   F1 Skoru (Macro): %{f1_macro*100:.2f}")
    print("\n📋 SINIFLANDIRMA RAPORU (Her Seviye İçin Detay)")
    print("-" * 60)
    
    labels = sorted(list(set(y_test)))
    target_names = [f"Seviye {i}" for i in labels]
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))
    
    print("🔢 KARMAŞIKLIK MATRİSİ (Satır: Gerçek, Sütun: Tahmin)")
    print("-" * 60)
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    header = "         " + "  ".join([f"Tahmin {i}" for i in labels])
    print(header)
    for i, row in zip(labels, cm):
        print(f"  Gerçek {i} | " + "    ".join(map(str, row)))
    for i, row in zip(labels, cm):
        print(f" Gerçek {i} | " + " ".join(map(str, row)))

    # --- BURAYA YAPIŞTIR (Hizaya Dikkat!) ---
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=target_names, yticklabels=target_names)
    plt.title('Model Tahmin Başarısı - Karmaşıklık Matrisi')
    plt.xlabel('Tahmin Edilen Seviye')
    plt.ylabel('Gerçek Seviye')
    plt.savefig('model_performans_grafigi.png') 
    print("\n📊 Performans grafiği 'model_performans_grafigi.png' olarak kaydedildi.")
    # ----------------------------------------

    print("\n✅ Test başarıyla tamamlandı.\n") # Bu satır en sonda kalabilir  
    print("\n✅ Test başarıyla tamamlandı.\n")

if __name__ == "__main__":
    test_et()
