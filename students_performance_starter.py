import joblib# type: ignore
import pandas as pd
import numpy as np# type: ignore
import os
import google.generativeai as genai# type: ignore
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline# type: ignore
from sklearn.preprocessing import StandardScaler

API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)

CSV_PATH = "StudentsPerformance_Extended.csv"
MODEL_PATH = "tavsiye_modeli_v4.joblib"

FEATURE_COLS = ['math score', 'physical score', 'chemical score', 'study_hours', 'sleep_hours']

# 1. Veri Setini Hazırlama ve Model Eğitimi (Random Forest)
def veri_setini_hazirla_ve_egit():
    if not os.path.exists(CSV_PATH):
        print(f"❌ HATA: {CSV_PATH} bulunamadı!")
        return
        
    df = pd.read_csv(CSV_PATH)

    if not os.path.exists(MODEL_PATH):
        print("🧠 Yeni verilere göre Makine Öğrenmesi Modeli (Random Forest) eğitiliyor...")
        from sklearn.ensemble import RandomForestClassifier# type: ignore
        from sklearn.model_selection import cross_val_score, StratifiedKFold# type: ignore
        X = df[FEATURE_COLS]
        
        # Etiket: Not ortalamasına göre 5. sınıfa ayır
        ortalama = df[["math score", "physical score", "chemical score"]].mean(axis=1)
        y = pd.qcut(ortalama, q=5, labels=False, duplicates="drop").astype(int)

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1))
        ])
        
        # Cross Validation skoru görmek için
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(pipeline, X, y, cv=cv, scoring='f1_macro', n_jobs=-1)
        print(f"   CV F1 Macro Skoru: {scores.mean():.4f}")

        pipeline.fit(X, y)
        stats = {col: {"mean": df[col].mean(), "std": df[col].std()} for col in FEATURE_COLS}
        joblib.dump({"pipeline": pipeline, "stats": stats, "cv_f1_macro_mean": float(scores.mean())}, MODEL_PATH)

# Z-Skoru Analizi
def z_skoru_durumu(skor, mean, std):
    z_score = (skor - mean) / std
    if z_score < -1: return "Çok Düşük (Kritik)"
    elif -1 <= z_score < -0.2: return "Ortalamanın Altında (Geliştirilmeli)"
    elif -0.2 <= z_score <= 0.5: return "Ortalama Seviyede"
    elif 0.5 < z_score <= 1.5: return "Ortalamanın Üstünde (İyi)"
    else: return "Çok Yüksek (Mükemmel)"

# 2. Yapay Zeka Tavsiye Motoru
def tavsiye_ver(mat, fiz, kim, calisma, uyku):
    print("\n⏳ Veriler analiz ediliyor ve Google sunucularına bağlanılıyor...\n")
    try:
        model_data = joblib.load(MODEL_PATH)
        pipe, stats = model_data["pipeline"], model_data["stats"]

        girdi = pd.DataFrame([[mat, fiz, kim, calisma, uyku]], columns=FEATURE_COLS)
        # Random Forest doğrudan 0-4 arası doğru seviyeyi verir
        gercek_seviye = int(pipe.predict(girdi)[0])

        analiz = {}
        veri_sozlugu = {
            'Matematik': (mat, 'math score'), 'Fizik': (fiz, 'physical score'), 
            'Kimya': (kim, 'chemical score'), 'Çalışma Süresi': (calisma, 'study_hours'), 
            'Uyku Süresi': (uyku, 'sleep_hours')
        }

        for isim, (skor, kolon) in veri_sozlugu.items():
            mean, std = stats[kolon]['mean'], stats[kolon]['std']
            analiz[isim] = z_skoru_durumu(skor, mean, std)

        # --- GÜNCELLENEN PROMPT KISMI ---
        prompt = f"""
        Sen uyarlanabilir bir öğrenme platformunun yapay zeka koçusun.
        Öğrencinin Kapsamlı Profili: Seviye {gercek_seviye}/4
        Akademik Durum: Matematik ({analiz['Matematik']}), Fizik ({analiz['Fizik']}), Kimya ({analiz['Kimya']})
        Fiziksel/Çevresel Durum: Günlük Ders Çalışma ({calisma} saat - {analiz['Çalışma Süresi']}), Günlük Uyku ({uyku} saat - {analiz['Uyku Süresi']}).

        Öğrenciye ismiyle hitap etme. Samimi ve motive edici bir dille aşağıdaki yapıda bir yanıt oluştur:
        
        1. Genel Değerlendirme ve Yaşam Stili:
        Öğrencinin notlarını, uyku ve ders çalışma süreleriyle harmanlayarak genel bir yorum yap. Verimlilik ve dinlenme dengesi üzerine nokta atışı bir tavsiye ver.
        
        2. Ders Bazlı Aksiyon Planı:
        - Matematik: Mevcut durumuna ({analiz['Matematik']}) göre ne yapmalı?
        - Fizik: Mevcut durumuna ({analiz['Fizik']}) göre nasıl bir yol izlemeli?
        - Kimya: Mevcut durumuna ({analiz['Kimya']}) göre hangi adımı atmalı?
        """
        # --------------------------------

        kullanilabilir_model = next((m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and "gemini" in m.name.lower()), None)
        if not kullanilabilir_model: return print("Uygun model bulunamadı.")

        model = genai.GenerativeModel(kullanilabilir_model)
        response = model.generate_content(prompt)
        
        print("="*75)
        print("🚀 YAPAY ZEKA KOÇUNUN DETAYLI ANALİZİ:")
        print("="*75)
        print(response.text)
        print("="*75)

    except Exception as e:
        print(f"Hata: {e}")

# Döngüsel Giriş Kontrolü
def gecerli_deger_al(mesaj, min_val, max_val):
    while True:
        try:
            deger = float(input(f"{mesaj} ({min_val}-{max_val}): "))
            if min_val <= deger <= max_val:
                return deger
            else:
                print(f"  -> HATA: Lütfen {min_val} ile {max_val} arasında bir değer giriniz!\n")
        except ValueError:
            print("  -> HATA: Lütfen sayısal bir değer giriniz!\n")

if __name__ == "__main__":
    veri_setini_hazirla_ve_egit()

    print("=== ÖĞRENCİ PROFİLİNİ OLUŞTUR ===")
    mat = gecerli_deger_al("Matematik Notu", 0, 100)
    fiz = gecerli_deger_al("Fizik Notu", 0, 100)
    kim = gecerli_deger_al("Kimya Notu", 0, 100)
    calisma = gecerli_deger_al("Günlük Ders Çalışma Süresi (Saat)", 0, 24)
    uyku = gecerli_deger_al("Günlük Uyku Süresi (Saat)", 0, 24)

    tavsiye_ver(mat, fiz, kim, calisma, uyku)
