"""
EduAI Güvenlik Test Paketi
==========================
Çalıştırma:
    python3 -m pytest tests/test_security.py -v
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# In-memory test veritabanı — StaticPool ile tek bağlantı paylaşılır (tablolar kaybolmaz)
_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_TEST_ENGINE)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


def _uid():
    return f"sec_{uuid.uuid4().hex[:8]}@test.com"


@pytest.fixture(scope="module")
def sec_client():
    from backend.database import Base, get_db
    from backend.models import User, Goal, Analysis  # noqa — tablo kayıtlarını tetikler
    Base.metadata.create_all(bind=_TEST_ENGINE)

    # Rate limit testlerde devre dışı — her sınıf aynı IP'den istek gönderiyor
    from backend.auth import limiter
    limiter.enabled = False

    with patch("backend.app.genai.GenerativeModel"), \
         patch("backend.app._pick_model_name", return_value="models/gemini-1.5-flash"), \
         patch("backend.app.genai.configure"):
        from backend.app import app
        app.dependency_overrides[get_db] = _override_get_db
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
        app.dependency_overrides.clear()

    limiter.enabled = True
    Base.metadata.drop_all(bind=_TEST_ENGINE)


# ── yardımcılar ──────────────────────────────────────────────────────────────

def _register(client, email=None, password="guvenli123"):
    return client.post("/auth/register", json={"email": email or _uid(), "password": password})


def _login(client, email, password="guvenli123"):
    return client.post("/auth/login", data={"username": email, "password": password})


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════
# 1. KİMLİK DOĞRULAMA GÜVENLİĞİ
# ══════════════════════════════════════════════

class TestKimlikDogrulama:

    def test_token_olmadan_goals_401(self, sec_client):
        assert sec_client.get("/api/goals").status_code == 401

    def test_rastgele_token_401(self, sec_client):
        assert sec_client.get("/api/goals", headers=_bearer("tamamen.gecersiz.token")).status_code == 401

    def test_yanlis_scheme_401(self, sec_client):
        # Bearer yerine Basic gönderilirse reddedilmeli
        assert sec_client.get("/api/goals", headers={"Authorization": "Basic abc123"}).status_code == 401

    def test_suresi_dolmus_jwt_401(self, sec_client):
        from backend.auth import SECRET_KEY, ALGORITHM
        expired = jwt.encode(
            {"sub": "test@test.com", "exp": datetime.utcnow() - timedelta(hours=1)},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        assert sec_client.get("/api/goals", headers=_bearer(expired)).status_code == 401

    def test_farkli_key_ile_imzali_token_401(self, sec_client):
        sahte = jwt.encode(
            {"sub": "admin@test.com", "exp": datetime.utcnow() + timedelta(days=1)},
            "tamamen-farkli-gizli-anahtar",
            algorithm="HS256",
        )
        assert sec_client.get("/api/goals", headers=_bearer(sahte)).status_code == 401

    def test_zayif_sifre_reddedilir(self, sec_client):
        r = _register(sec_client, password="123")
        assert r.status_code == 400

    def test_gecersiz_email_formati_422(self, sec_client):
        r = _register(sec_client, email="bu-email-degil")
        assert r.status_code == 422

    def test_ayni_email_tekrar_kayit_400(self, sec_client):
        email = _uid()
        _register(sec_client, email=email)
        assert _register(sec_client, email=email).status_code == 400

    def test_yanlis_sifre_ile_giris_reddedilir(self, sec_client):
        email = _uid()
        _register(sec_client, email=email, password="dogrusifre123")
        r = _login(sec_client, email, password="yanlissifre")
        assert r.status_code in (400, 401)

    def test_olmayan_hesap_ile_giris_reddedilir(self, sec_client):
        r = _login(sec_client, "olmayan@test.com", password="herhangi")
        assert r.status_code in (400, 401)

    def test_basarili_kayit_ve_giris_akisi(self, sec_client):
        email = _uid()
        reg = _register(sec_client, email=email)
        assert reg.status_code == 201
        assert "access_token" in reg.json()
        login = _login(sec_client, email)
        assert login.status_code == 200
        assert "access_token" in login.json()


# ══════════════════════════════════════════════
# 2. ŞİFRE GÜVENLİĞİ
# ══════════════════════════════════════════════

class TestSifreGuvenligi:

    def test_sifre_duz_metin_saklanmiyor(self, sec_client):
        from backend.models import User
        email = _uid()
        plain = "sifrem_gizli_456"
        _register(sec_client, email=email, password=plain)
        db = _TestSession()
        user = db.query(User).filter(User.email == email).first()
        db.close()
        assert user is not None
        assert user.password_hash != plain
        assert len(user.password_hash) > 30  # bcrypt hash ~60 karakter

    def test_ayni_sifre_farkli_hash_uretir(self, sec_client):
        """bcrypt rastgele tuz eklediğinden aynı parola iki farklı hash vermeli."""
        from backend.models import User
        e1, e2 = _uid(), _uid()
        same = "ayniSifre!99"
        _register(sec_client, email=e1, password=same)
        _register(sec_client, email=e2, password=same)
        db = _TestSession()
        u1 = db.query(User).filter(User.email == e1).first()
        u2 = db.query(User).filter(User.email == e2).first()
        db.close()
        assert u1.password_hash != u2.password_hash

    def test_bcrypt_prefix_kullaniliyor(self, sec_client):
        """Hash $2b$ ile başlamalı — bcrypt imzası."""
        from backend.models import User
        email = _uid()
        _register(sec_client, email=email, password="bcrypt_kontrol_456")
        db = _TestSession()
        user = db.query(User).filter(User.email == email).first()
        db.close()
        assert user.password_hash.startswith("$2")


# ══════════════════════════════════════════════
# 3. YETKİLENDİRME / IDOR
# ══════════════════════════════════════════════

class TestIDOR:
    """Kullanıcı A'nın verilerine kullanıcı B erişememeli (IDOR koruması)."""

    @pytest.fixture(scope="class")
    def iki_kullanici(self, sec_client):
        # A kaydı + hedef oluştur
        tok_a = _register(sec_client).json()["access_token"]
        goal_r = sec_client.post(
            "/api/goals",
            json={"baslik": "A'nın gizli hedefi", "aciklama": "özel"},
            headers=_bearer(tok_a),
        )
        assert goal_r.status_code == 201, f"Hedef oluşturulamadı: {goal_r.text}"
        goal_id = goal_r.json()["id"]
        # B kaydı
        tok_b = _register(sec_client).json()["access_token"]
        return {"tok_a": tok_a, "tok_b": tok_b, "goal_id": goal_id}

    def test_b_a_nin_hedeflerini_goremiyor(self, sec_client, iki_kullanici):
        r = sec_client.get("/api/goals", headers=_bearer(iki_kullanici["tok_b"]))
        ids = [g["id"] for g in r.json()["goals"]]
        assert iki_kullanici["goal_id"] not in ids

    def test_b_a_nin_hedefini_guncelleyemiyor(self, sec_client, iki_kullanici):
        r = sec_client.patch(
            f"/api/goals/{iki_kullanici['goal_id']}",
            json={"tamamlandi": 1},
            headers=_bearer(iki_kullanici["tok_b"]),
        )
        assert r.status_code == 404

    def test_b_a_nin_hedefini_sileyemiyor(self, sec_client, iki_kullanici):
        r = sec_client.delete(
            f"/api/goals/{iki_kullanici['goal_id']}",
            headers=_bearer(iki_kullanici["tok_b"]),
        )
        assert r.status_code == 404

    def test_olmayan_hedef_id_404(self, sec_client, iki_kullanici):
        r = sec_client.get("/api/goals", headers=_bearer(iki_kullanici["tok_a"]))
        assert r.status_code == 200
        # 999999 gibi büyük bir ID herhangi bir kullanıcı için bulunmamalı
        r2 = sec_client.delete("/api/goals/999999", headers=_bearer(iki_kullanici["tok_a"]))
        assert r2.status_code == 404


# ══════════════════════════════════════════════
# 4. GİRDİ DOĞRULAMA GÜVENLİĞİ
# ══════════════════════════════════════════════

class TestGirdiDogrulama:

    @pytest.fixture(scope="class")
    def tok(self, sec_client):
        return _register(sec_client).json()["access_token"]

    # ── Hedef endpoint girdi güvenliği ──

    def test_xss_payload_500_uretmiyor(self, sec_client, tok):
        r = sec_client.post(
            "/api/goals",
            json={"baslik": "<script>alert('xss')</script>"},
            headers=_bearer(tok),
        )
        assert r.status_code != 500

    def test_sql_injection_payload_500_uretmiyor(self, sec_client, tok):
        r = sec_client.post(
            "/api/goals",
            json={"baslik": "'; DROP TABLE users; --"},
            headers=_bearer(tok),
        )
        assert r.status_code != 500

    def test_cok_uzun_baslik_500_uretmiyor(self, sec_client, tok):
        r = sec_client.post(
            "/api/goals",
            json={"baslik": "A" * 10_000},
            headers=_bearer(tok),
        )
        assert r.status_code != 500

    def test_bos_baslik_400(self, sec_client, tok):
        r = sec_client.post("/api/goals", json={"baslik": "   "}, headers=_bearer(tok))
        assert r.status_code == 400

    def test_html_entity_baslik_500_uretmiyor(self, sec_client, tok):
        r = sec_client.post(
            "/api/goals",
            json={"baslik": "&lt;img src=x onerror=alert(1)&gt;"},
            headers=_bearer(tok),
        )
        assert r.status_code != 500

    # ── Analiz endpoint girdi güvenliği ──

    def test_analiz_uyku_sinir_asimi_422(self, sec_client):
        r = sec_client.post("/api/analyze", json={
            "notlar": {"mat": [75.0, 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
            "rutinler": {"uyku": 25.0, "calisma": 3.0},
        })
        assert r.status_code == 422

    def test_analiz_negatif_calisma_422(self, sec_client):
        r = sec_client.post("/api/analyze", json={
            "notlar": {"mat": [75.0, 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
            "rutinler": {"uyku": 7.0, "calisma": -1.0},
        })
        assert r.status_code == 422

    def test_analiz_metinsel_not_422(self, sec_client):
        r = sec_client.post("/api/analyze", json={
            "notlar": {"mat": ["yüz", 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
            "rutinler": {"uyku": 7.0, "calisma": 3.0},
        })
        assert r.status_code == 422

    def test_analiz_eksik_ders_422(self, sec_client):
        r = sec_client.post("/api/analyze", json={
            "notlar": {"mat": [75.0, 80.0, 70.0]},
            "rutinler": {"uyku": 7.0, "calisma": 3.0},
        })
        assert r.status_code == 422

    def test_analiz_json_injection_not_olarak_422(self, sec_client):
        r = sec_client.post("/api/analyze", json={
            "notlar": {"mat": [{"$ne": None}, 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
            "rutinler": {"uyku": 7.0, "calisma": 3.0},
        })
        assert r.status_code == 422

    def test_analiz_tek_not_422(self, sec_client):
        r = sec_client.post("/api/analyze", json={
            "notlar": {"mat": [75.0], "fiz": [60.0], "kim": [85.0]},
            "rutinler": {"uyku": 7.0, "calisma": 3.0},
        })
        assert r.status_code == 422


# ══════════════════════════════════════════════
# 5. RATE LİMİTİNG
# ══════════════════════════════════════════════

class TestRateLimiting:

    def test_register_rate_limit_aktif(self):
        """Kayıt endpoint'inin slowapi limit dekoratörü ile korunduğunu doğrula."""
        from backend import auth
        import inspect
        src = inspect.getsource(auth.register)
        assert "limiter.limit" in src or hasattr(auth.register, "__wrapped__")

    def test_login_rate_limit_aktif(self):
        """Giriş endpoint'inin slowapi limit dekoratörü ile korunduğunu doğrula."""
        from backend import auth
        import inspect
        src = inspect.getsource(auth.login)
        assert "limiter.limit" in src or hasattr(auth.login, "__wrapped__")

    def test_art_arda_basarisiz_giris_reddedilir(self, sec_client):
        """Var olmayan hesaba 5 art arda deneme — her biri 401/400 dönmeli."""
        email = f"brute_{uuid.uuid4().hex[:6]}@test.com"
        for _ in range(5):
            r = _login(sec_client, email, password="yanlissifre")
            assert r.status_code in (400, 401, 429)
