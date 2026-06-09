"""Alışkanlık modeli — yalnızca çalışma ve uyku saatinden performans seviyesini tahmin eder.

Notlu modelden (ml_context.py) tamamen bağımsızdır ve onu DEĞİŞTİRMEZ. Amaç dürüst,
sızıntısız (label leakage olmayan) bir tahmin:
    Girdi  = study_hours + sleep_hours   (notlar KULLANILMAZ)
    Hedef  = not ortalamasının 3 seviyesi: Düşük / Orta / Yüksek (0-2)

Notlar hedefi belirlerken kullanılır ama modele girdi olarak verilmez. Böylece
"öğrencinin alışkanlıkları başarısını ne kadar açıklıyor?" sorusunu dürüstçe ölçeriz.

Hedef 5 quintile yerine 3 seviye seçildi: alışkanlık tek başına tam dilimi
belirleyemez (F1 ~%30), ama "düşük/orta/yüksek" grubu makul bir doğrulukla
(F1 ~%50) ve hâlâ dürüst biçimde kestirir. Algoritma: Logistic Regression
(denenen tüm modeller arasında en iyi + en basit).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib  # type: ignore
import pandas as pd  # type: ignore

HABIT_FEATURES = ["study_hours", "sleep_hours"]
GRADE_COLS = ["math score", "physical score", "chemical score"]
HABIT_MODEL_FILE = "aliskanlik_modeli.joblib"
CSV_PATH = "StudentsPerformance_Extended.csv"
LEVEL_NAMES = ["Düşük", "Orta", "Yüksek"]


def make_labels(df: pd.DataFrame) -> pd.Series:
    """Not ortalamasına göre 3 seviye: Düşük(0) / Orta(1) / Yüksek(2)."""
    avg = df[GRADE_COLS].mean(axis=1)
    return pd.qcut(avg, q=3, labels=False, duplicates="drop").astype(int)


def grade_bins(df: pd.DataFrame) -> list[float]:
    """3 not-seviyesinin sınır değerleri (ortalama puan eşikleri). Fark analizinde
    bir öğrencinin not-seviyesini, alışkanlık-seviyesiyle aynı ölçekte hesaplamak için."""
    avg = df[GRADE_COLS].mean(axis=1)
    _, bins = pd.qcut(avg, q=3, labels=False, duplicates="drop", retbins=True)
    return [float(b) for b in bins]


def grade_tier_from_avg(avg: float, bins: list[float]) -> int:
    """Bir not ortalamasını 3 seviyeye (0/1/2) eşler — habit modeliyle aynı eşikler."""
    # bins = [min, t1, t2, max]; ilk/son sınır dışına taşan değerleri uçlara kıstır
    if avg <= bins[1]:
        return 0
    if avg <= bins[2]:
        return 1
    return 2


def tier_benchmarks(df: pd.DataFrame) -> dict[int, dict[str, float]]:
    """Her seviyedeki öğrencilerin TİPİK alışkanlığı (medyan çalışma/uyku saati).
    Fark analizinde somut, veriye dayalı hedef vermek için: 'Yüksek gruptakiler
    günde ~4 saat çalışıyor'. Medyan kullanılır (uçlardan etkilenmez)."""
    avg = df[GRADE_COLS].mean(axis=1)
    tier = pd.qcut(avg, q=3, labels=False, duplicates="drop").astype(int)
    out: dict[int, dict[str, float]] = {}
    for t in (0, 1, 2):
        sub = df[tier == t]
        out[t] = {
            "study": round(float(sub["study_hours"].median()), 1),
            "sleep": round(float(sub["sleep_hours"].median()), 1),
        }
    return out


def build_pipeline():
    """Alışkanlık modelinin pipeline'ı (eğitim ve dürüst değerlendirme aynısını kullanır)."""
    from sklearn.linear_model import LogisticRegression  # type: ignore
    from sklearn.pipeline import Pipeline  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore

    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                max_iter=1000, class_weight="balanced")),
        ]
    )


def train_habit_model(project_root: Path) -> dict[str, Any]:
    """Alışkanlık modelini eğitir, dürüst CV skoruyla birlikte kaydeder."""
    from sklearn.model_selection import cross_val_score  # type: ignore

    df = pd.read_csv(project_root / CSV_PATH).dropna()
    X = df[HABIT_FEATURES]
    y = make_labels(df)

    pipeline = build_pipeline()
    cv_f1 = float(cross_val_score(pipeline, X, y, cv=5, scoring="f1_macro").mean())
    pipeline.fit(X, y)

    bundle = {
        "pipeline": pipeline,
        "cv_f1_macro_mean": cv_f1,
        "features": HABIT_FEATURES,
        "grade_bins": grade_bins(df),
        "tier_benchmarks": tier_benchmarks(df),
    }
    joblib.dump(bundle, project_root / HABIT_MODEL_FILE)
    return bundle


def load_habit_model(project_root: Path) -> dict[str, Any] | None:
    """Kayıtlı alışkanlık modelini döndürür; yoksa None."""
    path = project_root / HABIT_MODEL_FILE
    return joblib.load(path) if path.is_file() else None


def ensure_habit_model(project_root: Path) -> dict[str, Any]:
    """Model dosyası yoksa eğitir, varsa yükler."""
    existing = load_habit_model(project_root)
    return existing if existing is not None else train_habit_model(project_root)
