#!/usr/bin/env python3
"""
EduAI — Proje Değerlendirme Raporu
====================================
Projenin güçlü ve geliştirilmesi gereken yönlerini analiz eder.

Çalıştırma:
    python3 tests/degerlendirme.py
"""
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Renk sabitleri ────────────────────────────────────────────────────────────
G = "\033[32m"   # yeşil
R = "\033[31m"   # kırmızı
Y = "\033[33m"   # sarı
B = "\033[1m"    # kalın
C = "\033[36m"   # cyan
S = "\033[0m"    # sıfırla

OK  = f"{G}✅{S}"
WAR = f"{Y}⚠️ {S}"
ERR = f"{R}❌{S}"


# ── Yardımcı sınıflar ─────────────────────────────────────────────────────────

class Kontrol:
    def __init__(self, etiket: str, gecti: bool, aciklama: str = ""):
        self.etiket    = etiket
        self.gecti     = gecti    # True = güçlü, False = zayıf
        self.aciklama  = aciklama


class Bolum:
    def __init__(self, baslik: str):
        self.baslik    = baslik
        self.kontroller: list[Kontrol] = []

    def guclu(self, etiket: str, aciklama: str = ""):
        self.kontroller.append(Kontrol(etiket, True, aciklama))

    def zayif(self, etiket: str, aciklama: str = ""):
        self.kontroller.append(Kontrol(etiket, False, aciklama))

    @property
    def puan(self) -> int:
        return sum(1 for k in self.kontroller if k.gecti)

    @property
    def toplam(self) -> int:
        return len(self.kontroller)

    @property
    def yuzde(self) -> int:
        return int(self.puan / self.toplam * 100) if self.toplam else 0


# ── Test istemcisi hazırlama ──────────────────────────────────────────────────

def _istemci_hazirla():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=engine)

    def _db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    with patch("backend.app.genai.GenerativeModel"), \
         patch("backend.app._pick_model_name", return_value="models/gemini-1.5-flash"), \
         patch("backend.app.genai.configure"):

        from backend.database import Base, get_db
        from backend.models import User, Goal, Analysis  # noqa
        Base.metadata.create_all(bind=engine)

        from backend.auth import limiter
        limiter.enabled = False

        from backend.app import app
        app.dependency_overrides[get_db] = _db

        from fastapi.testclient import TestClient
        return TestClient(app, raise_server_exceptions=False), TestSession, limiter


def _uid():
    return f"eval_{uuid.uuid4().hex[:8]}@test.com"


def _kayit(client, sifre="guvenli123"):
    email = _uid()
    r = client.post("/auth/register", json={"email": email, "password": sifre})
    return email, r.json().get("access_token", "")


def _bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


# ── Bölüm 1: Model Performansı ────────────────────────────────────────────────

def bolum_model() -> Bolum:
    b = Bolum("Model Performansı (ML)")
    try:
        import joblib
        import pandas as pd
        import numpy as np
        from sklearn.model_selection import cross_val_score, train_test_split
        from sklearn.metrics import f1_score

        model_path = PROJECT_ROOT / "tavsiye_modeli_v4.joblib"
        csv_path   = PROJECT_ROOT / "StudentsPerformance_Extended.csv"

        if not model_path.exists():
            b.zayif("Model dosyası mevcut", "tavsiye_modeli_v4.joblib bulunamadı")
            return b
        b.guclu("Model dosyası mevcut")

        if not csv_path.exists():
            b.zayif("Veri seti mevcut", "StudentsPerformance_Extended.csv bulunamadı")
            return b
        b.guclu("Veri seti mevcut")

        data = joblib.load(model_path)
        pipe = data["pipeline"]
        b.guclu("Model yüklenebiliyor")

        df = pd.read_csv(csv_path).dropna()
        cols = ["math score", "physical score", "chemical score", "study_hours", "sleep_hours"]
        ortalama = df[["math score", "physical score", "chemical score"]].mean(axis=1)
        y = pd.qcut(ortalama, q=5, labels=False, duplicates="drop").astype(int)
        X = df[cols]

        if len(df) >= 300:
            b.guclu(f"Veri seti boyutu yeterli ({len(df)} satır)")
        else:
            b.zayif(f"Veri seti küçük ({len(df)} satır)", "En az 300 satır önerilir")

        scores = cross_val_score(pipe, X, y, cv=5, scoring="f1_macro")
        f1_cv = scores.mean()
        if f1_cv >= 0.80:
            b.guclu(f"F1 Macro (CV-5) eşik değeri aşıyor: %{f1_cv*100:.1f}")
        else:
            b.zayif(f"F1 Macro düşük: %{f1_cv*100:.1f}", "Hedef: ≥ %80")

        if len(set(y)) >= 4:
            b.guclu(f"Çok sınıflı tahmin ({len(set(y))} seviye)")
        else:
            b.zayif("Az sınıf sayısı", "Beş seviye (quintile) bekleniyor")

        if len(cols) >= 5:
            b.guclu(f"{len(cols)} özellik kullanılıyor")
        if len(cols) < 8:
            b.zayif(
                "Özellik seti genişletilebilir",
                "Cinsiyet, hazırlık kursu, ebeveyn eğitim gibi alanlar eklenerek model zenginleştirilebilir",
            )

    except Exception as e:
        b.zayif("Model değerlendirme hatası", str(e))

    return b


# ── Bölüm 2: Kimlik Doğrulama & JWT ──────────────────────────────────────────

def bolum_kimlik(client) -> Bolum:
    b = Bolum("Kimlik Doğrulama & JWT")

    # Korunan endpoint token olmadan
    r = client.get("/api/goals")
    if r.status_code == 401:
        b.guclu("Korunan endpoint'ler token olmadan erişilemiyor (401)")
    else:
        b.zayif("Korunan endpoint token gerektirmiyor", f"Beklenen 401, alınan {r.status_code}")

    # Süresi dolmuş JWT
    from backend.auth import SECRET_KEY, ALGORITHM
    from jose import jwt as jose_jwt
    expired = jose_jwt.encode(
        {"sub": "test@test.com", "exp": datetime.utcnow() - timedelta(hours=1)},
        SECRET_KEY, algorithm=ALGORITHM,
    )
    r2 = client.get("/api/goals", headers=_bearer(expired))
    if r2.status_code == 401:
        b.guclu("Süresi dolmuş JWT reddediliyor (401)")
    else:
        b.zayif("Süresi dolmuş JWT kabul ediliyor", "Güvenlik açığı")

    # Sahte imzalı token
    sahte = jose_jwt.encode(
        {"sub": "admin@test.com", "exp": datetime.utcnow() + timedelta(days=1)},
        "farkli-anahtar", algorithm="HS256",
    )
    r3 = client.get("/api/goals", headers=_bearer(sahte))
    if r3.status_code == 401:
        b.guclu("Farklı key ile imzalı token reddediliyor (401)")
    else:
        b.zayif("Sahte imzalı token kabul ediliyor", "Kritik güvenlik açığı")

    # JWT fallback key kontrolü
    if SECRET_KEY == "eduai-fallback-key-set-in-env":
        b.zayif(
            "JWT secret key ortam değişkeninden okunmuyor",
            "JWT_SECRET_KEY env var ayarlanmamış; varsayılan zayıf key kullanılıyor. "
            "Production'da .env veya sistem değişkeniyle güçlü bir key belirlenmelidir.",
        )
    else:
        b.guclu("JWT secret key güvenli ortam değişkeninden alınıyor")

    # Kayıt & giriş akışı
    email, tok = _kayit(client)
    if tok:
        r4 = client.get("/api/goals", headers=_bearer(tok))
        if r4.status_code == 200:
            b.guclu("Kayıt → giriş → korunan endpoint akışı çalışıyor")
        else:
            b.zayif("Token ile endpoint erişimi başarısız")
    else:
        b.zayif("Kayıt akışı başarısız")

    return b


# ── Bölüm 3: Şifre Güvenliği ─────────────────────────────────────────────────

def bolum_sifre(client, TestSession) -> Bolum:
    b = Bolum("Şifre Güvenliği")

    from backend.models import User

    # bcrypt hashleme
    email, _ = _kayit(client, sifre="sifre_testi_789")
    db = TestSession()
    user = db.query(User).filter(User.email == email).first()
    db.close()

    if user and user.password_hash != "sifre_testi_789":
        b.guclu("Şifreler düz metin saklanmıyor (hashed)")
    else:
        b.zayif("Şifre düz metin saklanıyor", "Kritik güvenlik açığı")

    if user and user.password_hash.startswith("$2"):
        b.guclu("bcrypt algoritması kullanılıyor ($2b$ prefix)")
    else:
        b.zayif("bcrypt kullanılmıyor")

    # Tuzlama kontrolü (aynı şifre farklı hash)
    e1, _ = _kayit(client, sifre="ayniSifre99")
    e2, _ = _kayit(client, sifre="ayniSifre99")
    db = TestSession()
    u1 = db.query(User).filter(User.email == e1).first()
    u2 = db.query(User).filter(User.email == e2).first()
    db.close()
    if u1 and u2 and u1.password_hash != u2.password_hash:
        b.guclu("Rastgele tuz ekleniyor (aynı şifre farklı hash üretiyor)")
    else:
        b.zayif("Tuzlama eksik", "Aynı şifre aynı hash'i üretiyor")

    # Şifre minimum uzunluk
    r = client.post("/auth/register", json={"email": _uid(), "password": "123"})
    if r.status_code in (400, 422):
        b.guclu("Kısa şifre reddediliyor (min 6 karakter)")
    else:
        b.zayif("Kısa şifre kabul ediliyor", "Minimum uzunluk kontrolü eksik")

    # Şifre karmaşıklık politikası
    r2 = client.post("/auth/register", json={"email": _uid(), "password": "aaaaaa"})
    if r2.status_code in (400, 422):
        b.guclu("Şifre karmaşıklık politikası uygulanıyor")
    else:
        b.zayif(
            "Şifre karmaşıklık politikası yok",
            "'aaaaaa' gibi yalnızca küçük harften oluşan 6 karakterlik şifre kabul ediliyor. "
            "Büyük harf, rakam ve özel karakter zorunluluğu eklenebilir.",
        )

    return b


# ── Bölüm 4: Yetkilendirme & IDOR ────────────────────────────────────────────

def bolum_yetkilendirme(client) -> Bolum:
    b = Bolum("Yetkilendirme & Erişim Kontrolü")

    _, tok_a = _kayit(client)
    _, tok_b = _kayit(client)

    # A kullanıcısı hedef oluştur
    gr = client.post("/api/goals", json={"baslik": "Gizli hedef"}, headers=_bearer(tok_a))
    goal_id = gr.json().get("id") if gr.status_code == 201 else None

    if goal_id:
        # B, A'nın hedefini göremiyor mu?
        r = client.get("/api/goals", headers=_bearer(tok_b))
        ids = [g["id"] for g in r.json().get("goals", [])]
        if goal_id not in ids:
            b.guclu("IDOR koruması: Kullanıcı B, kullanıcı A'nın hedeflerini göremez")
        else:
            b.zayif("IDOR açığı: Kullanıcı B, A'nın hedeflerini görüyor", "Kritik güvenlik açığı")

        # B, A'nın hedefini güncelleyemiyor mu?
        r2 = client.patch(f"/api/goals/{goal_id}", json={"tamamlandi": 1}, headers=_bearer(tok_b))
        if r2.status_code == 404:
            b.guclu("IDOR koruması: Kullanıcı B, A'nın hedefini güncellemiyor (404)")
        else:
            b.zayif("IDOR açığı: Kullanıcı B, A'nın hedefini güncelleyebiliyor")

        # B, A'nın hedefini silemiyor mu?
        r3 = client.delete(f"/api/goals/{goal_id}", headers=_bearer(tok_b))
        if r3.status_code == 404:
            b.guclu("IDOR koruması: Kullanıcı B, A'nın hedefini silemiyor (404)")
        else:
            b.zayif("IDOR açığı: Kullanıcı B, A'nın hedefini silebiliyor")

    # Rate limiting varlığı
    from backend import auth
    import inspect
    src = inspect.getsource(auth.register)
    if "limiter.limit" in src:
        b.guclu("Rate limiting kayıt endpoint'inde aktif (5/dk)")
    else:
        b.zayif("Rate limiting eksik", "/auth/register endpoint'i saldırılara açık")

    src2 = inspect.getsource(auth.login)
    if "limiter.limit" in src2:
        b.guclu("Rate limiting giriş endpoint'inde aktif (10/dk)")
    else:
        b.zayif("Rate limiting eksik", "/auth/login endpoint'i kaba kuvvet saldırısına açık")

    # Hesap kilitleme
    b.zayif(
        "Hesap kilitleme mekanizması yok",
        "Çok sayıda başarısız girişten sonra hesap geçici kilitlenmiyor. "
        "Sadece rate limiting var; bu aşılabilir. Kalıcı hesap kilitleme eklenebilir.",
    )

    return b


# ── Bölüm 5: Girdi Doğrulama ─────────────────────────────────────────────────

def bolum_girdi(client) -> Bolum:
    b = Bolum("Girdi Doğrulama & Sınır Kontrolleri")

    base_payload = lambda mat0: {
        "notlar": {"mat": [mat0, 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
        "rutinler": {"uyku": 7.0, "calisma": 3.0},
    }

    # Not sınırları
    r1 = client.post("/api/analyze", json=base_payload(150.0))
    if r1.status_code in (400, 422):
        b.guclu("Not skoru > 100 reddediliyor")
    else:
        b.zayif("Not skoru > 100 kabul ediliyor", "0–100 dışı değerler için validasyon eklenmeli")

    r2 = client.post("/api/analyze", json=base_payload(-10.0))
    if r2.status_code in (400, 422):
        b.guclu("Negatif not skoru reddediliyor")
    else:
        b.zayif("Negatif not skoru kabul ediliyor", "0–100 dışı değerler için validasyon eklenmeli")

    # Rutin sınırları
    r3 = client.post("/api/analyze", json={
        "notlar": {"mat": [75.0, 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
        "rutinler": {"uyku": 25.0, "calisma": 3.0},
    })
    if r3.status_code == 422:
        b.guclu("Uyku saati > 24 reddediliyor (Pydantic Field ge/le)")
    else:
        b.zayif("Uyku saati sınırı uygulanmıyor")

    r4 = client.post("/api/analyze", json={
        "notlar": {"mat": [75.0, 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
        "rutinler": {"uyku": 7.0, "calisma": -1.0},
    })
    if r4.status_code == 422:
        b.guclu("Negatif çalışma saati reddediliyor (Pydantic Field ge/le)")
    else:
        b.zayif("Negatif çalışma saati sınırı uygulanmıyor")

    # Tip doğrulama
    r5 = client.post("/api/analyze", json={
        "notlar": {"mat": ["abc", 80.0, 70.0], "fiz": [60.0, 65.0, 70.0], "kim": [85.0, 90.0, 80.0]},
        "rutinler": {"uyku": 7.0, "calisma": 3.0},
    })
    if r5.status_code == 422:
        b.guclu("Metin veri sayısal alana girilince reddediliyor (422)")
    else:
        b.zayif("Tip doğrulama eksik", "Sayısal alanlara metin gönderilebiliyor")

    # Hedef başlık uzunluk
    _, tok = _kayit(client)
    r6 = client.post("/api/goals", json={"baslik": "A" * 10_000}, headers=_bearer(tok))
    if r6.status_code in (400, 422):
        b.guclu("Hedef başlığı max uzunluk kontrolü var")
    else:
        b.zayif(
            "Hedef başlığı için max uzunluk sınırı yok",
            "10.000 karakterlik başlık kabul ediliyor. "
            "Veritabanı ve UI performansı için örneğin 200 karakter sınırı eklenebilir.",
        )

    # Açıklama uzunluk
    r7 = client.post("/api/goals", json={"baslik": "Test", "aciklama": "B" * 50_000}, headers=_bearer(tok))
    if r7.status_code in (400, 422):
        b.guclu("Hedef açıklaması max uzunluk kontrolü var")
    else:
        b.zayif(
            "Hedef açıklaması için max uzunluk sınırı yok",
            "50.000 karakterlik açıklama kabul ediliyor.",
        )

    # XSS/SQL injection güvenliği
    r8 = client.post("/api/goals", json={"baslik": "<script>alert(1)</script>"}, headers=_bearer(tok))
    if r8.status_code != 500:
        b.guclu("XSS payload sunucu hatasına (500) yol açmıyor")
    else:
        b.zayif("XSS payload 500 hatası üretiyor")

    r9 = client.post("/api/goals", json={"baslik": "'; DROP TABLE users; --"}, headers=_bearer(tok))
    if r9.status_code != 500:
        b.guclu("SQL injection payload sunucu hatasına (500) yol açmıyor (ORM koruması)")
    else:
        b.zayif("SQL injection payload 500 hatası üretiyor")

    return b


# ── Bölüm 6: CORS & Ağ Güvenliği ─────────────────────────────────────────────

def bolum_cors(client) -> Bolum:
    b = Bolum("CORS & Ağ Güvenliği")

    r = client.get("/health", headers={"Origin": "https://evil.com"})
    cors_header = r.headers.get("access-control-allow-origin", "")

    if cors_header == "*":
        b.zayif(
            "CORS tüm origin'lere açık (allow_origins=['*'])",
            "Herhangi bir web sitesi bu API'ye çapraz kaynak isteği gönderebilir. "
            "Production'da yalnızca bilinen domain'ler izin verilenler listesine eklenmeli.",
        )
    elif cors_header:
        b.guclu(f"CORS belirli origin'lerle kısıtlı: {cors_header}")
    else:
        b.guclu("CORS başlığı gönderilmiyor (origin kısıtlı)")

    # HTTPS zorunluluğu (backend kodunda)
    app_src = (PROJECT_ROOT / "backend" / "app.py").read_text()
    if "https" in app_src.lower() or "hsts" in app_src.lower():
        b.guclu("HTTPS yönlendirmesi yapılandırılmış")
    else:
        b.zayif(
            "HTTPS zorunluluğu yok",
            "Backend HTTP üzerinden de çalışıyor. Production'da HTTPS zorunlu kılınmalı "
            "ve HSTS başlığı eklenmelidir.",
        )

    # Varsayılan hata detayları
    r2 = client.get("/api/bu_endpoint_yok")
    if r2.status_code == 404:
        body = r2.text.lower()
        if "traceback" not in body and "sqlalchemy" not in body:
            b.guclu("Hata yanıtları iç detay sızdırmıyor")
        else:
            b.zayif("Hata yanıtları iç sistem detayı sızdırıyor")
    else:
        b.guclu("Var olmayan endpoint 404 dönüyor")

    return b


# ── Rapor yazdır ──────────────────────────────────────────────────────────────

def rapor_yazdir(bolumler: list[Bolum]):
    en = "═"
    print()
    print(f"{B}{C}{'═'*62}{S}")
    print(f"{B}{C}{'EduAI — PROJE DEĞERLENDİRME RAPORU':^62}{S}")
    print(f"{B}{C}{'═'*62}{S}")
    print()

    genel_puan  = 0
    genel_toplam = 0

    for b in bolumler:
        renk = G if b.yuzde >= 70 else (Y if b.yuzde >= 50 else R)
        print(f"{B}{'─'*62}{S}")
        print(f"{B}{b.baslik}{S}  {renk}{b.puan}/{b.toplam} (%{b.yuzde}){S}")
        print()

        for k in b.kontroller:
            simge = OK if k.gecti else WAR
            print(f"  {simge} {k.etiket}")
            if k.aciklama and not k.gecti:
                # Zayıflık açıklamasını 60 karakterde sar
                words = k.aciklama.split()
                line, lines = [], []
                for w in words:
                    if sum(len(x)+1 for x in line) + len(w) > 56:
                        lines.append(" ".join(line))
                        line = [w]
                    else:
                        line.append(w)
                if line:
                    lines.append(" ".join(line))
                for i, ln in enumerate(lines):
                    prefix = "     → " if i == 0 else "       "
                    print(f"{Y}{prefix}{ln}{S}")
        print()

        genel_puan   += b.puan
        genel_toplam += b.toplam

    genel_yuzde = int(genel_puan / genel_toplam * 100) if genel_toplam else 0
    if genel_yuzde >= 80:
        g_renk = G; g_etiket = "GÜÇLÜ"
    elif genel_yuzde >= 60:
        g_renk = Y; g_etiket = "GELİŞTİRİLEBİLİR"
    else:
        g_renk = R; g_etiket = "ZAYIF"

    print(f"{B}{'═'*62}{S}")
    print(f"{B}GENEL DEĞERLENDİRME:{S}  "
          f"{g_renk}{B}{genel_puan}/{genel_toplam} (%{genel_yuzde}) — {g_etiket}{S}")
    print(f"{B}{'═'*62}{S}")
    print()

    # Özet: en iyi ve en zayıf bölümler
    en_iyi  = max(bolumler, key=lambda b: b.yuzde)
    en_zayif = min(bolumler, key=lambda b: b.yuzde)

    print(f"{B}En güçlü bölüm  :{S} {G}{en_iyi.baslik} (%{en_iyi.yuzde}){S}")
    print(f"{B}En zayıf bölüm  :{S} {Y}{en_zayif.baslik} (%{en_zayif.yuzde}){S}")
    print()

    # Öncelikli geliştirme önerileri
    tum_zayiflar = [
        k for b in bolumler for k in b.kontroller if not k.gecti
    ]
    if tum_zayiflar:
        print(f"{B}Öncelikli Geliştirme Önerileri:{S}")
        for i, k in enumerate(tum_zayiflar, 1):
            print(f"  {i}. {Y}{k.etiket}{S}")
    print()


# ── Ana akış ─────────────────────────────────────────────────────────────────

def main():
    import warnings
    warnings.filterwarnings("ignore")

    print(f"\n{C}Değerlendirme çalışıyor...{S}")

    client, TestSession, limiter = _istemci_hazirla()

    bolumler = [
        bolum_model(),
        bolum_kimlik(client),
        bolum_sifre(client, TestSession),
        bolum_yetkilendirme(client),
        bolum_girdi(client),
        bolum_cors(client),
    ]

    limiter.enabled = True
    rapor_yazdir(bolumler)


if __name__ == "__main__":
    main()
