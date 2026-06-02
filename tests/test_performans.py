"""
EduAI Performans & Yük Testleri
=================================
Çalıştırma:
    python3 -m pytest tests/test_performans.py -v
"""
import csv
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Eşik değerleri (ms) ───────────────────────────────────────────────────────
HEALTH_MAX_MS   = 100
GOALS_MAX_MS    = 200
ANALYZE_MAX_MS  = 2_000   # ML inference + overhead (mock'lu Gemini)

# ── Test verisi ───────────────────────────────────────────────────────────────
ANALIZ_PAYLOAD = {
    "notlar": {
        "mat": [75.0, 80.0, 70.0],
        "fiz": [60.0, 65.0, 70.0],
        "kim": [85.0, 90.0, 80.0],
    },
    "rutinler": {"uyku": 7.0, "calisma": 3.0},
}

_MOCK_ANALIZ = {
    "matematikDurum": "İyi", "matematikTrend": "+5 ↑",
    "matematikTavsiyeler": ["T1", "T2", "T3"],
    "fizikDurum": "Orta", "fizikTrend": "0 →",
    "fizikTavsiyeler": ["T1", "T2", "T3"],
    "kimyaDurum": "Çok İyi", "kimyaTrend": "+10 ↑",
    "kimyaTavsiyeler": ["T1", "T2", "T3"],
    "uykuDurum": "Normal", "uykuTavsiyeler": ["T1", "T2"],
    "calismaDurum": "Yeterli", "calismaTavsiyeler": ["T1", "T2"],
}


# ── Fixture ───────────────────────────────────────────────────────────────────

def _uid():
    return f"perf_{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture(scope="module")
def perf_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    def _fake_generate(prompt, *a, **kw):
        m = MagicMock()
        m.text = __import__("json").dumps(_MOCK_ANALIZ)
        return m

    with patch("backend.app.genai.GenerativeModel") as MockModel, \
         patch("backend.app._pick_model_name", return_value="models/gemini-1.5-flash"), \
         patch("backend.app.genai.configure"), \
         patch("backend.app.append_analyze_submission", return_value=True):

        instance = MagicMock()
        instance.generate_content.side_effect = _fake_generate
        MockModel.return_value = instance

        from backend.database import Base, get_db
        from backend.models import User, Goal, Analysis  # noqa
        Base.metadata.create_all(bind=engine)

        from backend.auth import limiter
        limiter.enabled = False

        from backend.app import app
        app.dependency_overrides[get_db] = _db

        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

        app.dependency_overrides.clear()
        limiter.enabled = True


@pytest.fixture(scope="module")
def perf_token(perf_client):
    r = perf_client.post(
        "/auth/register",
        json={"email": _uid(), "password": "performans123"},
    )
    return r.json()["access_token"]


def _bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


# ══════════════════════════════════════════════
# 1. YANIT SÜRESİ TESTLERİ
# ══════════════════════════════════════════════

class TestYanitSuresi:

    def test_health_endpoint_hizli(self, perf_client):
        start = time.perf_counter()
        r = perf_client.get("/api/health")
        ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert ms < HEALTH_MAX_MS, f"Health yavaş: {ms:.0f}ms (eşik: {HEALTH_MAX_MS}ms)"

    def test_goals_listele_hizli(self, perf_client, perf_token):
        start = time.perf_counter()
        r = perf_client.get("/api/goals", headers=_bearer(perf_token))
        ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert ms < GOALS_MAX_MS, f"Goals liste yavaş: {ms:.0f}ms (eşik: {GOALS_MAX_MS}ms)"

    def test_hedef_olusturma_hizli(self, perf_client, perf_token):
        start = time.perf_counter()
        r = perf_client.post(
            "/api/goals",
            json={"baslik": "Performans test hedefi"},
            headers=_bearer(perf_token),
        )
        ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 201
        assert ms < GOALS_MAX_MS, f"Hedef oluşturma yavaş: {ms:.0f}ms (eşik: {GOALS_MAX_MS}ms)"

    def test_analiz_yanit_suresi(self, perf_client):
        # İlk çağrı ML modelini ısıtabilir; gerçek süreyi 2. çağrıda ölç
        perf_client.post("/api/analyze", json=ANALIZ_PAYLOAD)
        start = time.perf_counter()
        r = perf_client.post("/api/analyze", json=ANALIZ_PAYLOAD)
        ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert ms < ANALYZE_MAX_MS, f"Analiz yavaş: {ms:.0f}ms (eşik: {ANALYZE_MAX_MS}ms)"

    def test_ardisik_5_analiz_tutarli_sure(self, perf_client):
        """5 ardışık istek arasında ciddi yavaşlama olmamalı."""
        sureler = []
        for _ in range(5):
            start = time.perf_counter()
            perf_client.post("/api/analyze", json=ANALIZ_PAYLOAD)
            sureler.append((time.perf_counter() - start) * 1000)

        ort = sum(sureler) / len(sureler)
        maks = max(sureler)
        # En yavaş istek, ortalamadan 5× fazla olmamalı
        assert maks < ort * 5, (
            f"Tutarsız yanıt süresi — ort: {ort:.0f}ms, maks: {maks:.0f}ms"
        )


# ══════════════════════════════════════════════
# 2. EŞ ZAMANLILIK TESTLERİ
# ══════════════════════════════════════════════

class TestEsZamanlilik:

    def test_10_esuzamanli_analiz_istegi(self, perf_client):
        """10 eş zamanlı analiz isteği — hepsi 200 dönmeli."""
        def istek(_):
            return perf_client.post("/api/analyze", json=ANALIZ_PAYLOAD)

        with ThreadPoolExecutor(max_workers=10) as ex:
            sonuclar = list(ex.map(istek, range(10)))

        basarisiz = [r for r in sonuclar if r.status_code != 200]
        assert len(basarisiz) == 0, (
            f"{len(basarisiz)}/10 istek başarısız: "
            f"{[r.status_code for r in basarisiz]}"
        )

    def test_10_ardisik_kayit_istegi(self, perf_client):
        """10 ardışık benzersiz e-posta kaydı — hepsi 201 dönmeli.

        Not: SQLite in-memory DB eş zamanlı yazımı desteklemez; production'da
        PostgreSQL/MySQL ile gerçek concurrent test yapılabilir.
        """
        sonuclar = [
            perf_client.post(
                "/auth/register",
                json={"email": _uid(), "password": "concurrent123"},
            )
            for _ in range(10)
        ]
        basarili = [r for r in sonuclar if r.status_code == 201]
        assert len(basarili) == 10, f"Sadece {len(basarili)}/10 kayıt başarılı"

    def test_ardisik_goals_crud_hiz_tutarli(self, perf_client, perf_token):
        """5 ardışık hedef oluşturma her biri GOALS_MAX_MS altında kalmalı."""
        sureler = []
        idler = []
        for i in range(5):
            start = time.perf_counter()
            r = perf_client.post(
                "/api/goals",
                json={"baslik": f"Ardışık hedef {i}"},
                headers=_bearer(perf_token),
            )
            sureler.append((time.perf_counter() - start) * 1000)
            assert r.status_code == 201
            idler.append(r.json()["id"])

        # Hiçbir istek eşiği aşmamalı
        yavas = [ms for ms in sureler if ms > GOALS_MAX_MS]
        assert not yavas, f"{len(yavas)}/5 istek yavaş: {[f'{m:.0f}ms' for m in yavas]}"

        # Tüm ID'ler benzersiz
        assert len(set(idler)) == 5, "Ardışık oluşturmada çakışan ID var"


# ══════════════════════════════════════════════
# 3. CSV THREAD-SAFETY TESTLERİ
# ══════════════════════════════════════════════

class TestCSVThreadGuvenligi:

    def test_paralel_csv_yazimi_veri_kaybetmez(self, tmp_path):
        """20 thread aynı anda yazarsa tüm satırlar korunmalı."""
        from backend.submission_csv import append_analyze_submission

        # submission_csv yalnızca 5 kolona yazar; başlık bu 5 kolon olmalı
        csv_file = tmp_path / "StudentsPerformance_Extended.csv"
        header = ["math score", "physical score", "chemical score", "study_hours", "sleep_hours"]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=header).writeheader()

        ortalamalar = {"mat": 75, "fiz": 65, "kim": 80}

        def yaz(_):
            return append_analyze_submission(tmp_path, ortalamalar, 3.0, 7.0)

        N = 20
        with ThreadPoolExecutor(max_workers=N) as ex:
            sonuclar = list(ex.map(yaz, range(N)))

        assert all(sonuclar), "Bazı CSV yazımları başarısız döndü"

        with open(csv_file, newline="", encoding="utf-8") as f:
            satirlar = list(csv.reader(f))
        # Başlık + N veri satırı (boş satır filtrele)
        satirlar = [s for s in satirlar if any(s)]
        assert len(satirlar) == N + 1, (
            f"Beklenen {N + 1} satır, bulunan {len(satirlar)} — veri kaybı var"
        )

    def test_paralel_csv_yazimi_veri_bozulmaz(self, tmp_path):
        """Eş zamanlı yazımlarda satırlar karışmamalı (partial write yok)."""
        from backend.submission_csv import append_analyze_submission

        csv_file = tmp_path / "StudentsPerformance_Extended.csv"
        header = ["math score", "physical score", "chemical score", "study_hours", "sleep_hours"]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=header).writeheader()

        def yaz(i):
            return append_analyze_submission(
                tmp_path,
                {"mat": i, "fiz": i, "kim": i},
                float(i % 8),
                float(i % 10),
            )

        N = 30
        with ThreadPoolExecutor(max_workers=N) as ex:
            list(ex.map(yaz, range(N)))

        # Her satırın parse edilebilir olduğunu kontrol et
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for satir in reader:
                assert "math score" in satir, f"Bozuk satır: {satir}"
                assert satir["math score"].strip() != "", "Boş math score"
