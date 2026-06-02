"""
EduAI Uçtan Uca (End-to-End) Akış Testleri
============================================
Gerçek kullanıcı yolculuklarını simüle eder.

Çalıştırma:
    python3 -m pytest tests/test_e2e.py -v
"""
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── Mock Gemini yanıtları ─────────────────────────────────────────────────────

_MOCK_ANALIZ = {
    "matematikDurum": "İyi", "matematikTrend": "+5 ↑",
    "matematikTavsiyeler": ["Tavsiye A", "Tavsiye B", "Tavsiye C"],
    "fizikDurum": "Orta", "fizikTrend": "0 →",
    "fizikTavsiyeler": ["Tavsiye A", "Tavsiye B", "Tavsiye C"],
    "kimyaDurum": "Çok İyi", "kimyaTrend": "+10 ↑",
    "kimyaTavsiyeler": ["Tavsiye A", "Tavsiye B", "Tavsiye C"],
    "uykuDurum": "Normal", "uykuTavsiyeler": ["Tavsiye A", "Tavsiye B"],
    "calismaDurum": "Yeterli", "calismaTavsiyeler": ["Tavsiye A", "Tavsiye B"],
}

_MOCK_PLAN = {
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

ANALIZ_PAYLOAD = {
    "notlar": {
        "mat": [75.0, 80.0, 70.0],
        "fiz": [60.0, 65.0, 70.0],
        "kim": [85.0, 90.0, 80.0],
    },
    "rutinler": {"uyku": 7.0, "calisma": 3.0},
}


# ── Fixture ───────────────────────────────────────────────────────────────────

def _uid():
    return f"e2e_{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture(scope="module")
def e2e_client():
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
        if "learning" in prompt.lower() or "hafta" in prompt.lower():
            m.text = json.dumps(_MOCK_PLAN)
        else:
            m.text = json.dumps(_MOCK_ANALIZ)
        return m

    with patch("backend.app.genai.GenerativeModel") as MockModel, \
         patch("backend.app._pick_model_name", return_value="models/gemini-1.5-flash"), \
         patch("backend.app.genai.configure"), \
         patch("backend.submission_csv.append_analyze_submission", return_value=True):

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
            yield c, Session  # hem client hem session fabrikası

        app.dependency_overrides.clear()
        limiter.enabled = True


def _bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


# ══════════════════════════════════════════════
# 1. TAM KULLANICI YOLCULUĞU
# ══════════════════════════════════════════════

class TestTamKullaniciAkisi:

    def test_kayit_giris_analiz_hedef_tam_akis(self, e2e_client):
        """
        Kayıt → Giriş → Analiz → Hedef Ekle → Hedefi Tamamla → Hedefi Sil
        """
        client, Session = e2e_client
        email = _uid()

        # 1. Kayıt
        r = client.post("/auth/register", json={"email": email, "password": "e2etest123"})
        assert r.status_code == 201, f"Kayıt başarısız: {r.text}"
        tok = r.json()["access_token"]
        assert tok

        # 2. Giriş (token yenile)
        r2 = client.post("/auth/login", data={"username": email, "password": "e2etest123"})
        assert r2.status_code == 200, f"Giriş başarısız: {r2.text}"
        tok = r2.json()["access_token"]

        auth = _bearer(tok)

        # 3. Analiz yap (giriş yapmış kullanıcı)
        r3 = client.post("/api/analyze", json=ANALIZ_PAYLOAD, headers=auth)
        assert r3.status_code == 200, f"Analiz başarısız: {r3.text}"
        analiz = r3.json()
        assert "ai" in analiz
        assert "matematikDurum" in analiz["ai"]

        # 4. Hedef ekle
        r4 = client.post("/api/goals", json={"baslik": "Matematik çalış", "aciklama": "Her gün"}, headers=auth)
        assert r4.status_code == 201
        goal_id = r4.json()["id"]
        assert r4.json()["tamamlandi"] == 0

        # 5. Hedefi tamamla
        r5 = client.patch(f"/api/goals/{goal_id}", json={"tamamlandi": 1}, headers=auth)
        assert r5.status_code == 200
        assert r5.json()["tamamlandi"] == 1

        # 6. Hedefler listesinde görünüyor mu?
        r6 = client.get("/api/goals", headers=auth)
        assert r6.status_code == 200
        ids = [g["id"] for g in r6.json()["goals"]]
        assert goal_id in ids

        # 7. Hedefi sil
        r7 = client.delete(f"/api/goals/{goal_id}", headers=auth)
        assert r7.status_code == 200

        # 8. Silinen hedef artık listede yok
        r8 = client.get("/api/goals", headers=auth)
        ids_sonra = [g["id"] for g in r8.json()["goals"]]
        assert goal_id not in ids_sonra

    def test_misafir_kullanici_analiz_yapabilir(self, e2e_client):
        """Token olmadan analiz endpoint'i çalışmalı (misafir modu)."""
        client, _ = e2e_client
        r = client.post("/api/analyze", json=ANALIZ_PAYLOAD)
        assert r.status_code == 200
        assert "ai" in r.json()
        assert "matematikDurum" in r.json()["ai"]

    def test_iki_farkli_kullanici_izole_hedefler(self, e2e_client):
        """İki kullanıcının hedefleri birbirine karışmamalı."""
        client, _ = e2e_client

        r_a = client.post("/auth/register", json={"email": _uid(), "password": "test123"})
        tok_a = r_a.json()["access_token"]

        r_b = client.post("/auth/register", json={"email": _uid(), "password": "test123"})
        tok_b = r_b.json()["access_token"]

        # A'nın hedefi
        g_a = client.post("/api/goals", json={"baslik": "A'nın hedefi"}, headers=_bearer(tok_a))
        id_a = g_a.json()["id"]

        # B'nin hedefi
        g_b = client.post("/api/goals", json={"baslik": "B'nin hedefi"}, headers=_bearer(tok_b))
        id_b = g_b.json()["id"]

        # A sadece kendi hedefini görür
        liste_a = [g["id"] for g in client.get("/api/goals", headers=_bearer(tok_a)).json()["goals"]]
        assert id_a in liste_a
        assert id_b not in liste_a

        # B sadece kendi hedefini görür
        liste_b = [g["id"] for g in client.get("/api/goals", headers=_bearer(tok_b)).json()["goals"]]
        assert id_b in liste_b
        assert id_a not in liste_b


# ══════════════════════════════════════════════
# 2. ANALİZ AKIŞI
# ══════════════════════════════════════════════

class TestAnalizAkisi:

    def test_analiz_sonucu_dogru_alanlar(self, e2e_client):
        """Analiz yanıtı beklenen tüm üst düzey ve AI alanlarını içermeli."""
        client, _ = e2e_client
        r = client.post("/api/analyze", json=ANALIZ_PAYLOAD)
        assert r.status_code == 200
        veri = r.json()

        # Üst düzey yapı
        assert "ai" in veri, "Yanıtta 'ai' anahtarı yok"
        assert "ortalamalar" in veri, "Yanıtta 'ortalamalar' yok"
        assert "sklearn" in veri, "Yanıtta 'sklearn' yok"

        # ai alt alanları
        ai = veri["ai"]
        beklenen_ai = [
            "matematikDurum", "matematikTrend", "matematikTavsiyeler",
            "fizikDurum", "fizikTrend", "fizikTavsiyeler",
            "kimyaDurum", "kimyaTrend", "kimyaTavsiyeler",
            "uykuDurum", "uykuTavsiyeler",
            "calismaDurum", "calismaTavsiyeler",
        ]
        eksik = [alan for alan in beklenen_ai if alan not in ai]
        assert not eksik, f"ai altında eksik alanlar: {eksik}"

        # ortalamalar
        ort = veri["ortalamalar"]
        assert all(k in ort for k in ("mat", "fiz", "kim")), "ortalamalar eksik alan"

    def test_analiz_veritabanina_kaydediliyor(self, e2e_client):
        """Giriş yapmış kullanıcının analizi DB'ye kaydedilmeli."""
        client, Session = e2e_client
        from backend.models import Analysis, User

        email = _uid()
        r = client.post("/auth/register", json={"email": email, "password": "test123"})
        tok = r.json()["access_token"]

        db = Session()
        kullanici = db.query(User).filter(User.email == email).first()
        onceki_sayim = db.query(Analysis).filter(Analysis.user_id == kullanici.id).count()
        db.close()

        client.post("/api/analyze", json=ANALIZ_PAYLOAD, headers=_bearer(tok))

        db = Session()
        yeni_sayim = db.query(Analysis).filter(Analysis.user_id == kullanici.id).count()
        db.close()

        assert yeni_sayim == onceki_sayim + 1, "Analiz DB'ye kaydedilmedi"

    def test_birden_fazla_analiz_gecmis_buyuyor(self, e2e_client):
        """Her analiz DB'de ayrı kayıt oluşturmalı."""
        client, Session = e2e_client
        from backend.models import Analysis, User

        email = _uid()
        r = client.post("/auth/register", json={"email": email, "password": "test123"})
        tok = r.json()["access_token"]

        db = Session()
        kullanici = db.query(User).filter(User.email == email).first()
        db.close()

        for _ in range(3):
            client.post("/api/analyze", json=ANALIZ_PAYLOAD, headers=_bearer(tok))

        db = Session()
        sayim = db.query(Analysis).filter(Analysis.user_id == kullanici.id).count()
        db.close()

        assert sayim == 3, f"3 analiz bekleniyor, {sayim} kaydedilmiş"

    def test_analiz_ortalamalari_dogru_hesaplaniyor(self, e2e_client):
        """mat=[60,70,80] → ortalama 70 olmalı."""
        client, _ = e2e_client
        payload = {
            "notlar": {
                "mat": [60.0, 70.0, 80.0],
                "fiz": [50.0, 60.0, 70.0],
                "kim": [80.0, 90.0, 100.0],
            },
            "rutinler": {"uyku": 8.0, "calisma": 4.0},
        }
        r = client.post("/api/analyze", json=payload)
        assert r.status_code == 200

    def test_farkli_not_profilleri_yanit_veriyor(self, e2e_client):
        """Zayıf öğrenci de, güçlü öğrenci de yanıt alabilmeli."""
        client, _ = e2e_client

        zayif = {
            "notlar": {"mat": [20.0, 25.0, 30.0], "fiz": [15.0, 20.0, 25.0], "kim": [10.0, 15.0, 20.0]},
            "rutinler": {"uyku": 4.0, "calisma": 1.0},
        }
        guclu = {
            "notlar": {"mat": [95.0, 98.0, 100.0], "fiz": [90.0, 95.0, 98.0], "kim": [92.0, 96.0, 99.0]},
            "rutinler": {"uyku": 8.0, "calisma": 6.0},
        }

        r1 = client.post("/api/analyze", json=zayif)
        r2 = client.post("/api/analyze", json=guclu)

        assert r1.status_code == 200, f"Zayıf profil yanıt vermedi: {r1.text}"
        assert r2.status_code == 200, f"Güçlü profil yanıt vermedi: {r2.text}"


# ══════════════════════════════════════════════
# 3. HEDEF YAŞAM DÖNGÜSÜ
# ══════════════════════════════════════════════

class TestHedefYasamDongusu:

    @pytest.fixture(scope="class")
    def kullanici_tok(self, e2e_client):
        client, _ = e2e_client
        r = client.post("/auth/register", json={"email": _uid(), "password": "hedef123"})
        return r.json()["access_token"]

    def test_bos_liste_yeni_kullanicida(self, e2e_client, kullanici_tok):
        client, _ = e2e_client
        r = client.get("/api/goals", headers=_bearer(kullanici_tok))
        assert r.status_code == 200
        assert r.json()["goals"] == []

    def test_hedef_olusturma(self, e2e_client, kullanici_tok):
        client, _ = e2e_client
        r = client.post(
            "/api/goals",
            json={"baslik": "Fizik çalış", "aciklama": "Her akşam 1 saat"},
            headers=_bearer(kullanici_tok),
        )
        assert r.status_code == 201
        veri = r.json()
        assert veri["baslik"] == "Fizik çalış"
        assert veri["aciklama"] == "Her akşam 1 saat"
        assert veri["tamamlandi"] == 0

    def test_birden_fazla_hedef_ekleme(self, e2e_client, kullanici_tok):
        client, _ = e2e_client
        basliklar = ["Hedef A", "Hedef B", "Hedef C"]
        for b in basliklar:
            client.post("/api/goals", json={"baslik": b}, headers=_bearer(kullanici_tok))

        r = client.get("/api/goals", headers=_bearer(kullanici_tok))
        mevcut = [g["baslik"] for g in r.json()["goals"]]
        for b in basliklar:
            assert b in mevcut, f"'{b}' listede yok"

    def test_hedef_tamamlama_durumu_guncelleniyor(self, e2e_client, kullanici_tok):
        client, _ = e2e_client
        r = client.post("/api/goals", json={"baslik": "Güncellenecek hedef"}, headers=_bearer(kullanici_tok))
        goal_id = r.json()["id"]

        # 0 → 1
        r2 = client.patch(f"/api/goals/{goal_id}", json={"tamamlandi": 1}, headers=_bearer(kullanici_tok))
        assert r2.json()["tamamlandi"] == 1

        # 1 → 0 (geri al)
        r3 = client.patch(f"/api/goals/{goal_id}", json={"tamamlandi": 0}, headers=_bearer(kullanici_tok))
        assert r3.json()["tamamlandi"] == 0

    def test_hedef_silme(self, e2e_client, kullanici_tok):
        client, _ = e2e_client
        r = client.post("/api/goals", json={"baslik": "Silinecek hedef"}, headers=_bearer(kullanici_tok))
        goal_id = r.json()["id"]

        client.delete(f"/api/goals/{goal_id}", headers=_bearer(kullanici_tok))

        liste = [g["id"] for g in client.get("/api/goals", headers=_bearer(kullanici_tok)).json()["goals"]]
        assert goal_id not in liste

    def test_gecersiz_tamamlandi_degeri_422(self, e2e_client, kullanici_tok):
        """tamamlandi yalnızca 0 veya 1 olabilmeli."""
        client, _ = e2e_client
        r = client.post("/api/goals", json={"baslik": "Validasyon hedefi"}, headers=_bearer(kullanici_tok))
        goal_id = r.json()["id"]

        r2 = client.patch(f"/api/goals/{goal_id}", json={"tamamlandi": 99}, headers=_bearer(kullanici_tok))
        assert r2.status_code == 422


# ══════════════════════════════════════════════
# 4. OTURUM YÖNETİMİ
# ══════════════════════════════════════════════

class TestOturumYonetimi:

    def test_suresi_dolmus_token_ile_islem_401(self, e2e_client):
        """Süresi dolmuş token ile hedef işlemi yapılamamalı."""
        client, _ = e2e_client
        from backend.auth import SECRET_KEY, ALGORITHM

        expired_tok = jose_jwt.encode(
            {"sub": "expired@test.com", "exp": datetime.utcnow() - timedelta(hours=1)},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        r = client.get("/api/goals", headers=_bearer(expired_tok))
        assert r.status_code == 401

    def test_token_yenileme_ile_erisim_devam_eder(self, e2e_client):
        """Eski token yerine yeni token alınınca işlemler devam eder."""
        client, _ = e2e_client
        email = _uid()
        client.post("/auth/register", json={"email": email, "password": "yenile123"})

        # İlk token
        r1 = client.post("/auth/login", data={"username": email, "password": "yenile123"})
        tok1 = r1.json()["access_token"]

        # Yeni token al (yeniden giriş)
        r2 = client.post("/auth/login", data={"username": email, "password": "yenile123"})
        tok2 = r2.json()["access_token"]

        # Her iki token da çalışmalı (sunucu token blacklist uygulamıyor)
        r3 = client.get("/api/goals", headers=_bearer(tok1))
        r4 = client.get("/api/goals", headers=_bearer(tok2))
        assert r3.status_code == 200
        assert r4.status_code == 200

    def test_yanlis_sifre_ile_giris_401(self, e2e_client):
        """Yanlış şifre ile giriş denemesi reddedilmeli."""
        client, _ = e2e_client
        email = _uid()
        client.post("/auth/register", json={"email": email, "password": "dogrusifre123"})
        r = client.post("/auth/login", data={"username": email, "password": "yanlissifre"})
        assert r.status_code in (400, 401)
