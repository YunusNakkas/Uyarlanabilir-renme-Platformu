"""
EduAI Backend Test Paketi
=========================
Çalıştırma:
    python3 -m pytest tests/test_suite.py -v
    python3 -m pytest tests/test_suite.py -v --tb=short --html=test_report.html
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.metrics import f1_score, classification_report
from sklearn.model_selection import cross_val_score, train_test_split

# Proje kökünü path'e ekle
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ──────────────────────────────────────────────
# Sabitler
# ──────────────────────────────────────────────
MODEL_PATH   = PROJECT_ROOT / "tavsiye_modeli_v4.joblib"
CSV_PATH     = PROJECT_ROOT / "StudentsPerformance_Extended.csv"
FEATURE_COLS = ["math score", "physical score", "chemical score", "study_hours", "sleep_hours"]
F1_THRESHOLD = 0.80

VALID_PAYLOAD = {
    "notlar": {
        "mat": [75.0, 80.0, 70.0],
        "fiz": [60.0, 65.0, 70.0],
        "kim": [85.0, 90.0, 80.0],
    },
    "rutinler": {"uyku": 7.0, "calisma": 3.0},
}

# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def model_data():
    assert MODEL_PATH.exists(), f"Model bulunamadı: {MODEL_PATH}"
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="session")
def dataset():
    assert CSV_PATH.exists(), f"CSV bulunamadı: {CSV_PATH}"
    df = pd.read_csv(CSV_PATH).dropna()
    ortalama = df[["math score", "physical score", "chemical score"]].mean(axis=1)
    y = pd.qcut(ortalama, q=5, labels=False, duplicates="drop").astype(int)
    X = df[FEATURE_COLS]
    return X, y, df


@pytest.fixture(scope="session")
def test_split(dataset):
    X, y, _ = dataset
    return train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient — Gemini çağrıları mock'lanır."""
    mock_response = {
        "matematikDurum": "İyi",
        "matematikTrend": "+5 ↑",
        "matematikTavsiyeler": ["Tavsiye 1", "Tavsiye 2", "Tavsiye 3"],
        "fizikDurum": "Orta",
        "fizikTrend": "0 →",
        "fizikTavsiyeler": ["Tavsiye 1", "Tavsiye 2", "Tavsiye 3"],
        "kimyaDurum": "Çok İyi",
        "kimyaTrend": "+10 ↑",
        "kimyaTavsiyeler": ["Tavsiye 1", "Tavsiye 2", "Tavsiye 3"],
        "uykuDurum": "Normal",
        "uykuTavsiyeler": ["Tavsiye 1", "Tavsiye 2"],
        "calismaDurum": "Yeterli",
        "calismaTavsiyeler": ["Tavsiye 1", "Tavsiye 2"],
    }
    mock_lp = {
        "ozet": "Genel özet.",
        "haftalikToplamSaat": 15,
        "haftalar": [
            {
                "hafta": i,
                "odak": f"Hafta {i} odağı",
                "gorevler": {
                    "matematik": ["Görev A"],
                    "fizik": ["Görev B"],
                    "kimya": ["Görev C"],
                },
                "motivasyon": "Başarabilirsin!",
            }
            for i in range(1, 5)
        ],
    }

    def fake_generate(prompt, *a, **kw):
        m = MagicMock()
        if "learning" in prompt.lower() or "hafta" in prompt.lower() or "öğrenme" in prompt.lower():
            m.text = json.dumps(mock_lp)
        else:
            m.text = json.dumps(mock_response)
        return m

    with patch("backend.app.genai.GenerativeModel") as mock_model_cls, \
         patch("backend.app._pick_model_name", return_value="models/gemini-1.5-flash"), \
         patch("backend.app.genai.configure"):
        instance = MagicMock()
        instance.generate_content.side_effect = fake_generate
        mock_model_cls.return_value = instance

        from backend.app import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


# ══════════════════════════════════════════════
# 1. MODEL PERFORMANS TESTLERİ
# ══════════════════════════════════════════════

class TestModelPerformance:

    def test_model_dosyasi_mevcut(self):
        assert MODEL_PATH.exists(), "tavsiye_modeli_v4.joblib bulunamadı"

    def test_model_yuklenebilir(self, model_data):
        assert "pipeline" in model_data, "model_data içinde 'pipeline' anahtarı yok"

    def test_csv_mevcut(self):
        assert CSV_PATH.exists(), "StudentsPerformance_Extended.csv bulunamadı"

    def test_csv_gerekli_kolonlar(self, dataset):
        _, _, df = dataset
        for col in FEATURE_COLS:
            assert col in df.columns, f"Kolon eksik: {col}"

    def test_veri_boyutu(self, dataset):
        X, y, df = dataset
        assert len(df) >= 100, f"Veri seti çok küçük: {len(df)} satır"

    def test_f1_macro_esik_degeri_cv(self, model_data, dataset):
        """CV ile doğru değerlendirme — model tüm veriyle eğitildiğinden
        train/test split yerine cross_val_score kullanılır."""
        pipeline = model_data["pipeline"]
        X, y, _ = dataset
        scores = cross_val_score(pipeline, X, y, cv=5, scoring="f1_macro")
        f1_cv = scores.mean()
        assert f1_cv >= F1_THRESHOLD, f"CV F1 Macro {f1_cv:.4f} < eşik {F1_THRESHOLD}"

    def test_f1_duzgun_egitim_test_ayrimi(self, model_data, test_split, dataset):
        """Temiz değerlendirme: sadece train seti üzerinde yeniden fit, test setinde ölç."""
        from sklearn.base import clone
        pipeline = model_data["pipeline"]
        X_train, X_test, y_train, y_test = test_split
        fresh = clone(pipeline)
        fresh.fit(X_train, y_train)
        y_pred = fresh.predict(X_test)
        f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
        assert f1 >= F1_THRESHOLD, f"Temiz F1 Macro {f1:.4f} < eşik {F1_THRESHOLD}"

    def test_f1_makul_siniflar(self, model_data, test_split):
        """Her sınıf için temiz eğitimle F1 ≥ 0.70 olmalı."""
        from sklearn.base import clone
        pipeline = model_data["pipeline"]
        X_train, X_test, y_train, y_test = test_split
        fresh = clone(pipeline)
        fresh.fit(X_train, y_train)
        y_pred = fresh.predict(X_test)
        labels = sorted(y_test.unique())
        f1_per = f1_score(y_test, y_pred, average=None, labels=labels, zero_division=0)
        for lbl, score in zip(labels, f1_per):
            assert score >= 0.70, f"Seviye {lbl} F1 skoru düşük: {score:.4f}"

    def test_tahmin_aralik(self, model_data, dataset):
        """Tahminler 0-4 arasında olmalı."""
        pipeline = model_data["pipeline"]
        X, y, _ = dataset
        preds = pipeline.predict(X.head(50))
        assert set(preds).issubset({0, 1, 2, 3, 4}), f"Beklenmeyen tahmin değerleri: {set(preds)}"

    def test_capraz_dogrulama(self, model_data, dataset):
        """3-fold CV F1 macro ≥ 0.75 olmalı."""
        pipeline = model_data["pipeline"]
        X, y, _ = dataset
        scores = cross_val_score(pipeline, X, y, cv=3, scoring="f1_macro")
        assert scores.mean() >= 0.75, f"CV ortalaması düşük: {scores.mean():.4f}"


# ══════════════════════════════════════════════
# 2. API ENDPOINT TESTLERİ
# ══════════════════════════════════════════════

class TestHealthEndpoint:

    def test_health_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_json_yapisı(self, client):
        r = client.get("/api/health")
        data = r.json()
        assert "ok" in data
        assert data["ok"] is True

    def test_health_gemini_key_alani(self, client):
        r = client.get("/api/health")
        assert "gemini_key_loaded" in r.json()


class TestAnalyzeEndpoint:

    def test_gecerli_istek_200(self, client):
        r = client.post("/api/analyze", json=VALID_PAYLOAD)
        assert r.status_code == 200, r.text

    def test_yanit_alanlari(self, client):
        r = client.post("/api/analyze", json=VALID_PAYLOAD)
        data = r.json()
        assert "ai" in data
        assert "ortalamalar" in data
        assert "sklearn" in data

    def test_ortalamalar_hesaplama(self, client):
        r = client.post("/api/analyze", json=VALID_PAYLOAD)
        o = r.json()["ortalamalar"]
        assert o["mat"] == 75   # (75+80+70)/3 = 75
        assert o["fiz"] == 65   # (60+65+70)/3 = 65
        assert o["kim"] == 85   # (85+90+80)/3 = 85

    def test_not_siniri_asagi(self, client):
        payload = {**VALID_PAYLOAD, "notlar": {"mat": [-1.0, 50.0, 50.0], "fiz": [50.0, 50.0, 50.0], "kim": [50.0, 50.0, 50.0]}}
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 400

    def test_not_siniri_yukari(self, client):
        payload = {**VALID_PAYLOAD, "notlar": {"mat": [101.0, 50.0, 50.0], "fiz": [50.0, 50.0, 50.0], "kim": [50.0, 50.0, 50.0]}}
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 400

    def test_eksik_alan(self, client):
        r = client.post("/api/analyze", json={"notlar": {"mat": [70, 75, 80]}})
        assert r.status_code == 422

    def test_bos_istek(self, client):
        r = client.post("/api/analyze", json={})
        assert r.status_code == 422

    def test_sifir_notlar(self, client):
        payload = {
            "notlar": {"mat": [0.0, 0.0, 0.0], "fiz": [0.0, 0.0, 0.0], "kim": [0.0, 0.0, 0.0]},
            "rutinler": {"uyku": 8.0, "calisma": 2.0},
        }
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 200

    def test_maksimum_notlar(self, client):
        payload = {
            "notlar": {"mat": [100.0, 100.0, 100.0], "fiz": [100.0, 100.0, 100.0], "kim": [100.0, 100.0, 100.0]},
            "rutinler": {"uyku": 8.0, "calisma": 6.0},
        }
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 200

    def test_uyku_sinir_asimi(self, client):
        payload = {**VALID_PAYLOAD, "rutinler": {"uyku": 25.0, "calisma": 3.0}}
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 422

    def test_calisma_negatif(self, client):
        payload = {**VALID_PAYLOAD, "rutinler": {"uyku": 7.0, "calisma": -1.0}}
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 422

    def test_iki_not_gonderilince_422(self, client):
        payload = {**VALID_PAYLOAD, "notlar": {"mat": [70.0, 80.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]}}
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 422

    def test_dort_not_gonderilince_422(self, client):
        payload = {**VALID_PAYLOAD, "notlar": {"mat": [70.0, 80.0, 75.0, 90.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]}}
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 422


class TestLearningPathEndpoint:

    def test_gecerli_istek_200(self, client):
        r = client.post("/api/learning-path", json=VALID_PAYLOAD)
        assert r.status_code == 200, r.text

    def test_plan_alani_var(self, client):
        r = client.post("/api/learning-path", json=VALID_PAYLOAD)
        assert "plan" in r.json()

    def test_plan_haftalar_listesi(self, client):
        r = client.post("/api/learning-path", json=VALID_PAYLOAD)
        plan = r.json()["plan"]
        assert "haftalar" in plan
        assert isinstance(plan["haftalar"], list)

    def test_dort_hafta_donuyor(self, client):
        r = client.post("/api/learning-path", json=VALID_PAYLOAD)
        haftalar = r.json()["plan"]["haftalar"]
        assert len(haftalar) == 4

    def test_hafta_gorevler_yapisi(self, client):
        r = client.post("/api/learning-path", json=VALID_PAYLOAD)
        for h in r.json()["plan"]["haftalar"]:
            assert "gorevler" in h
            assert "matematik" in h["gorevler"]
            assert "fizik" in h["gorevler"]
            assert "kimya" in h["gorevler"]

    def test_eksik_payload_422(self, client):
        r = client.post("/api/learning-path", json={})
        assert r.status_code == 422


class TestStaticServing:

    def test_anasayfa_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_login_sayfasi_200(self, client):
        r = client.get("/login")
        assert r.status_code == 200

    def test_reset_sayfasi_200(self, client):
        r = client.get("/reset")
        assert r.status_code == 200

    def test_css_200(self, client):
        r = client.get("/style.css")
        assert r.status_code == 200

    def test_js_200(self, client):
        r = client.get("/js/app.js")
        assert r.status_code == 200

    def test_olmayan_sayfa_404(self, client):
        r = client.get("/olmayan-sayfa-xyz")
        assert r.status_code == 404


# ══════════════════════════════════════════════
# 3. VERİ DOĞRULAMA TESTLERİ
# ══════════════════════════════════════════════

class TestDataIntegrity:

    def test_csv_bos_satirlar(self, dataset):
        _, _, df = dataset
        assert df.isnull().sum().sum() == 0, "CSV'de NaN değerler var (dropna sonrası)"

    def test_notlar_aralik(self, dataset):
        _, _, df = dataset
        for col in ["math score", "physical score", "chemical score"]:
            assert df[col].between(0, 100).all(), f"{col} 0-100 dışında değer içeriyor"

    def test_uyku_saatleri_mantikli(self, dataset):
        _, _, df = dataset
        if "sleep_hours" in df.columns:
            assert df["sleep_hours"].between(0, 24).all(), "sleep_hours 0-24 dışında"

    def test_calisma_saatleri_mantikli(self, dataset):
        _, _, df = dataset
        if "study_hours" in df.columns:
            assert df["study_hours"].between(0, 24).all(), "study_hours 0-24 dışında"

    def test_etiket_dagilimi(self, dataset):
        """Her sınıf en az 10 örnek içermeli."""
        _, y, _ = dataset
        counts = y.value_counts()
        for lbl, cnt in counts.items():
            assert cnt >= 10, f"Sınıf {lbl} az örnek: {cnt}"
