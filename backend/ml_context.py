"""KMeans + z-skor: model yoksa CSV'den eğitilir; her analizde predict çalışır."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib# type: ignore
import numpy as np
import pandas as pd# type: ignore
from sklearn.cluster import KMeans# type: ignore
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler# type: ignore

FEATURE_COLS = ["math score", "physical score", "chemical score", "study_hours", "sleep_hours"]
CSV_PATH = "StudentsPerformance_Extended.csv"
MODEL_FILE = "tavsiye_modeli_v4.joblib"


def z_skoru_durumu(skor: float, mean: float, std: float) -> str:
    if std == 0 or std is None or np.isnan(std):
        return "Ortalama Seviyede"
    z_score = (skor - mean) / std
    if z_score < -1:
        return "Çok Düşük (Kritik)"
    if -1 <= z_score < -0.2:
        return "Ortalamanın Altında (Geliştirilmeli)"
    if -0.2 <= z_score <= 0.5:
        return "Ortalama Seviyede"
    if 0.5 < z_score <= 1.5:
        return "Ortalamanın Üstünde (İyi)"
    return "Çok Yüksek (Mükemmel)"


def load_model_bundle(project_root: Path) -> dict[str, Any] | None:
    path = project_root / MODEL_FILE
    if not path.is_file():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def ensure_sklearn_model(project_root: Path) -> None:
    """Model dosyası yoksa genişletilmiş CSV'yi kullanarak Random Forest modelini eğitir."""
    model_path = project_root / MODEL_FILE
    if model_path.is_file():
        return

    extended_path = project_root / CSV_PATH

    if not extended_path.is_file():
        raise FileNotFoundError(
            f"Proje kökünde {CSV_PATH} bulunamadı; scikit-learn modeli eğitilemiyor."
        )

    df = pd.read_csv(extended_path)
    X = df[FEATURE_COLS]
    
    from sklearn.ensemble import RandomForestClassifier# type: ignore
    # Etiket (y) oluşumu: Not ortalamasına göre 5 dilim 0-4
    ortalama = df[["math score", "physical score", "chemical score"]].mean(axis=1)
    y = pd.qcut(ortalama, q=5, labels=False, duplicates="drop").astype(int)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1)),
        ]
    )
    # Kaydetmeden önce dürüst bir genelleme skoru ölç (5 kat çapraz doğrulama, macro F1)
    from sklearn.model_selection import cross_val_score  # type: ignore
    try:
        cv_f1 = float(cross_val_score(pipeline, X, y, cv=5, scoring="f1_macro").mean())
    except Exception:
        cv_f1 = None

    pipeline.fit(X, y)
    stats = {col: {"mean": float(df[col].mean()), "std": float(df[col].std())} for col in FEATURE_COLS}
    joblib.dump(
        {"pipeline": pipeline, "stats": stats, "cv_f1_macro_mean": cv_f1},
        model_path,
    )


def ml_context_paragraph(
    project_root: Path,
    mat_avg: int,
    fiz_avg: int,
    kim_avg: int,
    calisma: float,
    uyku: float,
) -> tuple[str | None, dict[str, Any]]:
    data = load_model_bundle(project_root)
    if not data:
        return None, {"sklearn_ran": False, "hata": "model_yuklenemedi"}
    try:
        pipe = data["pipeline"]
        stats: dict = data["stats"]
        # V4 Random Forest mappinge ihtiyaç duymaz, direkt 0-4 tahmin eder
        mapping: dict[int, int] = data.get("cluster_mapping", {})
    except (KeyError, TypeError):
        return None, {"sklearn_ran": False, "hata": "model_bozuk"}

    girdi = pd.DataFrame(
        [[mat_avg, fiz_avg, kim_avg, calisma, uyku]],
        columns=FEATURE_COLS,
    )
    raw_cluster = int(pipe.predict(girdi)[0])
    gercek_seviye = int(mapping.get(raw_cluster, raw_cluster))

    veri_sozlugu = {
        "Matematik": (mat_avg, "math score"),
        "Fizik": (fiz_avg, "physical score"),
        "Kimya": (kim_avg, "chemical score"),
        "Çalışma Süresi": (calisma, "study_hours"),
        "Uyku Süresi": (uyku, "sleep_hours"),
    }
    analiz: dict[str, str] = {}
    for isim, (skor, kolon) in veri_sozlugu.items():
        s = stats.get(kolon) or {}
        mean, std = s.get("mean", 0.0), s.get("std", 1.0)
        analiz[isim] = z_skoru_durumu(float(skor), float(mean), float(std))

    paragraf = (
        f"Veri setine göre öğrenci kümesi seviyesi: {gercek_seviye}/4. "
        f"İstatistiksel profil: Matematik ({analiz['Matematik']}), Fizik ({analiz['Fizik']}), "
        f"Kimya ({analiz['Kimya']}), Günlük çalışma ({calisma} saat — {analiz['Çalışma Süresi']}), "
        f"Uyku ({uyku} saat — {analiz['Uyku Süresi']}). Bu bağlamı tavsiyelerinde dikkate al."
    )
    meta = {
        "sklearn_ran": True,
        "kmeans_raw_cluster": raw_cluster,
        "ogrenci_profili_seviyesi_0_4": gercek_seviye,
        "z_skor_ozetleri": {k: v for k, v in analiz.items()},
    }
    return paragraf, meta
