"""
EduAI analiz API'si: Gemini ile JSON tavsiye üretir; isteğe bağlı ML bağlamı ekler.
Çalıştırma (proje kökünden): uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
Tarayıcı: http://127.0.0.1:8000/ (Live Server yerine; CSV yazılınca sayfa yenilenmez)
Ayarlar: proje kökünde local.env veya gemini_api_key.txt (TextEdit: Biçim → Düz Metin yapın, .rtf kullanmayın)
"""
from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

from typing import Optional

import google.generativeai as genai# type: ignore
from dotenv import load_dotenv# type: ignore
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool# type: ignore
from fastapi.middleware.cors import CORSMiddleware# type: ignore
from fastapi.responses import FileResponse# type: ignore
from fastapi.staticfiles import StaticFiles# type: ignore
from jose import JWTError, jwt# type: ignore
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session# type: ignore

from .auth import ALGORITHM, SECRET_KEY, get_current_user, router as auth_router
from .email_sender import EmailConfigError, EmailSendError, send_report_email
from .llm import LLMError, groq_generate
from .logger import logger
from .database import get_db, init_db
from .gap_analysis import analyze_gap, gap_context_paragraph
from .ml_context import ensure_sklearn_model, ml_context_paragraph# type: ignore
from .models import Analysis, Goal, User
from .submission_csv import append_analyze_submission

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = Path(__file__).resolve().parent
_FRONTEND_DIR = PROJECT_ROOT / "frontend"
# Gizli anahtarlar (TextEdit bazen local.env.rtf kaydeder — o çalışmaz, düz metin gerekir)
# override=True: terminalde boş GEMINI_API_KEY export edilmişse dosyadaki değer yine de okunur
for _p in (
    PROJECT_ROOT / "local.env",
    PROJECT_ROOT / "local.env.txt",
    _BACKEND_DIR / "local.env",
    _BACKEND_DIR / "local.env.txt",
):
    load_dotenv(_p, override=True)


def _load_gemini_key_from_plain_file() -> None:
    """GEMINI_API_KEY yoksa: tek satırlık düz metin dosyası (TextEdit ile kolay)."""
    if (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip():
        return
    key_path = PROJECT_ROOT / "gemini_api_key.txt"
    if not key_path.is_file():
        return
    try:
        raw = key_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            os.environ["GEMINI_API_KEY"] = line
            return


_load_gemini_key_from_plain_file()


class NotlarIn(BaseModel):
    mat: list[float] = Field(..., min_length=3, max_length=3)
    fiz: list[float] = Field(..., min_length=3, max_length=3)
    kim: list[float] = Field(..., min_length=3, max_length=3)


class RutinlerIn(BaseModel):
    uyku: float = Field(..., ge=0, le=24)
    calisma: float = Field(..., ge=0, le=24)


class AnalyzeRequest(BaseModel):
    notlar: NotlarIn
    rutinler: RutinlerIn


def _avg(three: list[float]) -> int:
    return int(round(sum(three) / 3))


def _build_prompt(
    notlar: NotlarIn,
    rutinler: RutinlerIn,
    ortalamalar: dict[str, int],
    ml_extra: str | None,
) -> str:
    n = notlar
    r = rutinler
    o = ortalamalar
    extra = f"\nEk bağlam: {ml_extra}\n" if ml_extra else ""
    return f"""
            Sen uzman ve analitik bir eğitim koçusun. Öğrencinin notları:
            Matematik: 1.Sınav: {n.mat[0]}, 2.Sınav: {n.mat[1]}, Sözlü: {n.mat[2]} (Ort: {o["mat"]})
            Fizik: 1.Sınav: {n.fiz[0]}, 2.Sınav: {n.fiz[1]}, Sözlü: {n.fiz[2]} (Ort: {o["fiz"]})
            Kimya: 1.Sınav: {n.kim[0]}, 2.Sınav: {n.kim[1]}, Sözlü: {n.kim[2]} (Ort: {o["kim"]})

            Öğrencinin günlük rutinleri:
            Uyku: {r.uyku} saat
            Ders Çalışma: {r.calisma} saat
            {extra}
            Öğrenciye her ders için ve genel rutini için çok detaylı, uygulanabilir ve kapsamlı tavsiyeler ver. Sadece "daha çok çalış" gibi basit cümleler KULLANMA. Nasıl bir çalışma stratejisi izlemeli, uyku ve çalışma saati dengesini nasıl sağlamalı detaylandır.

            Aşağıdaki JSON formatında, her ders için ve rutin için en az 3 adet ve her biri 2-3 cümleden oluşan UZUN VE DETAYLI tavsiyeler döndür. Ekstra metin yazma, sadece JSON formatı döndür. DİKKAT: JSON içinde "..." (üç nokta) gibi kısaltmalar kullanma, JSON tamamen hatasız olmalı:
            {{
                "matematikDurum": "Kısa özet",
                "matematikTrend": "Örn: +13 ↑",
                "matematikTavsiyeler": ["Gerçek tavsiye 1", "Gerçek tavsiye 2", "Gerçek tavsiye 3"],
                "fizikDurum": "Kısa özet",
                "fizikTrend": "Örn: -4 ↓",
                "fizikTavsiyeler": ["Gerçek tavsiye 1", "Gerçek tavsiye 2", "Gerçek tavsiye 3"],
                "kimyaDurum": "Kısa özet",
                "kimyaTrend": "Örn: +4 ↑",
                "kimyaTavsiyeler": ["Gerçek tavsiye 1", "Gerçek tavsiye 2", "Gerçek tavsiye 3"],
                "uykuDurum": "Kısa özet",
                "uykuTavsiyeler": ["Uyku ile ilgili gerçek tavsiye 1", "Tavsiye 2"],
                "calismaDurum": "Kısa özet",
                "calismaTavsiyeler": ["Ders çalışma süresi ile ilgili gerçek tavsiye 1", "Tavsiye 2"]
            }}"""


def _gemini_text(response) -> str:
    try:
        return response.text or ""
    except ValueError:
        cands = getattr(response, "candidates", None) or []
        if not cands:
            return ""
        parts = getattr(cands[0].content, "parts", None) or []
        return "".join(getattr(p, "text", "") or "" for p in parts)


def _parse_ai_json(text: str) -> dict:
    t = text.replace("```json", "").replace("```JSON", "").replace("```", "").strip()
    t = re.sub(r",\s*([}\]])", r"\1", t)
    return json.loads(t)


_cached_gemini_model: str | None = None


def _pick_model_name() -> str:
    global _cached_gemini_model
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not key:
        raise HTTPException(
            status_code=500,
            detail=(
                "GEMINI_API_KEY yüklenemedi. Proje köküne (index.html'in yanına) şunlardan birini koyun: "
                "(1) Düz metin local.env, içinde GEMINI_API_KEY=anahtar — TextEdit'te Biçim→Düz Metin; .rtf olmamalı. "
                "(2) Veya düz metin gemini_api_key.txt, tek satırda sadece anahtar."
            ),
        )
    genai.configure(api_key=key)
    if _cached_gemini_model:
        return _cached_gemini_model

    # local.env: GEMINI_MODEL=gemini-2.0-flash ile elle sabitlenebilir
    override = (os.environ.get("GEMINI_MODEL") or "").strip()
    if override:
        _cached_gemini_model = override if override.startswith("models/") else f"models/{override}"
        return _cached_gemini_model

    # generateContent destekleyen tüm gemini modellerini topla
    available = []
    for m in genai.list_models():
        methods = [x.lower() for x in (getattr(m, "supported_generation_methods", None) or [])]
        if "generatecontent" in methods and "gemini" in (m.name or "").lower():
            available.append(m.name)

    # Ücretsiz katmanda çalışan modelleri TERCİH et; 2.5-* faturalandırma ister (403).
    for pref in ("gemini-2.0-flash-001", "gemini-2.0-flash", "gemini-2.0-flash-lite",
                 "gemini-1.5-flash", "gemini-1.5-flash-latest"):
        for name in available:
            # 2.5'i atla — ücretsiz katmanda PERMISSION_DENIED
            if "2.5" in name:
                continue
            if pref in name:
                _cached_gemini_model = name
                return name

    # Tercih eşleşmediyse 2.5 olmayan ilk modele düş
    for name in available:
        if "2.5" not in name:
            _cached_gemini_model = name
            return name

    raise HTTPException(status_code=503, detail="Uygun Gemini modeli bulunamadı")


def _gemini_available() -> bool:
    return bool((os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip())


def _groq_available() -> bool:
    return bool((os.environ.get("GROQ_API_KEY") or "").strip())


def _fallback_enabled() -> bool:
    """LLM_FALLBACK=0/false ile kapatılabilir; varsayılan açık."""
    return (os.environ.get("LLM_FALLBACK") or "1").strip().lower() not in ("0", "false", "no")


def _gemini_generate(prompt: str) -> tuple[str, str]:
    """Gemini'den ham metin üretir. Tüm hataları LLMError'a çevirir (fallback için tek tip)."""
    try:
        model_name = _pick_model_name()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
    except HTTPException as e:
        raise LLMError(f"Gemini: {e.detail}") from e
    except Exception as e:
        raise LLMError(f"Gemini hatası: {e!s}") from e
    return _gemini_text(response).strip(), model_name


def _generate_raw(prompt: str) -> tuple[str, str]:
    """Ham metin üretir; birincil sağlayıcı başarısızsa diğerine otomatik düşer.

    Sıra: LLM_PROVIDER=groq ise Groq birincil, aksi halde Gemini birincil. Yedek sağlayıcı
    yalnızca anahtarı tanımlıysa ve LLM_FALLBACK kapalı değilse denenir. İkisi de
    patlarsa toplanan hatalar HTTPException(502) olarak yükseltilir.
    """
    # (ad, üretici fn, kullanılabilirlik) — sırayla denenir
    providers = {
        "groq": (groq_generate, _groq_available),
        "gemini": (_gemini_generate, _gemini_available),
    }
    # Birincil sağlayıcı: yalnızca LLM_PROVIDER=groq ise Groq, aksi halde Gemini.
    provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
    order = ["groq", "gemini"] if provider == "groq" else ["gemini", "groq"]
    if not _fallback_enabled():
        order = order[:1]

    errors: list[str] = []
    attempted = False
    for name in order:
        fn, available = providers[name]
        if not available():
            continue
        attempted = True
        try:
            raw, model_name = fn(prompt)
            if errors:  # birincil patlamıştı, yedeğe düştük
                logger.warning("LLM fallback → %s kullanıldı (önceki: %s)", name, " | ".join(errors))
            return raw.strip(), model_name
        except LLMError as e:
            errors.append(f"{name}: {e!s}")
            logger.warning("LLM sağlayıcı '%s' başarısız: %s", name, e)

    if not attempted:
        raise HTTPException(
            status_code=503,
            detail="Hiçbir LLM sağlayıcısı yapılandırılmamış (GEMINI_API_KEY veya GROQ_API_KEY gerekli).",
        )
    raise HTTPException(status_code=502, detail="Tüm LLM sağlayıcıları başarısız: " + " | ".join(errors))


app = FastAPI(title="EduAI Backend", version="1.0.0")
init_db()
app.include_router(auth_router)


def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Token varsa kullanıcıyı döndür; yoksa/geçersizse None (analiz yine de çalışsın)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        return None
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_static(request, call_next):
    """HTML/JS/CSS'i tarayıcı önbelleğe almasın — değişiklikler hemen görünür."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".html", ".js", ".css")) or path in ("/login", "/reset"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.get("/api/health")
def health():
    key_ok = bool((os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip())
    return {"ok": True, "gemini_key_loaded": key_ok}


@app.post("/api/analyze")
def analyze(
    body: AnalyzeRequest,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    for ders, vals in (
        ("mat", body.notlar.mat),
        ("fiz", body.notlar.fiz),
        ("kim", body.notlar.kim),
    ):
        for v in vals:
            if v < 0 or v > 100:
                raise HTTPException(status_code=400, detail=f"{ders} notları 0–100 aralığında olmalı")

    ortalamalar = {
        "mat": _avg(body.notlar.mat),
        "fiz": _avg(body.notlar.fiz),
        "kim": _avg(body.notlar.kim),
    }
    try:
        ensure_sklearn_model(PROJECT_ROOT)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scikit-learn modeli hazırlanamadı: {e!s}",
        ) from e

    ml_extra, sk_meta = ml_context_paragraph(
        PROJECT_ROOT,
        ortalamalar["mat"],
        ortalamalar["fiz"],
        ortalamalar["kim"],
        body.rutinler.calisma,
        body.rutinler.uyku,
    )
    if not ml_extra:
        raise HTTPException(
            status_code=500,
            detail="Scikit-learn modeli yüklendi ancak tahmin üretilemedi.",
        )

    # Fark analizi: notlardan gelen seviye ile alışkanlıktan tahmin edilen seviyeyi kıyaslar.
    # Tavsiyeye değer kattığı için Gemini bağlamına eklenir; başarısız olursa analiz aksamaz.
    gap = None
    try:
        gap = analyze_gap(
            PROJECT_ROOT,
            ortalamalar["mat"], ortalamalar["fiz"], ortalamalar["kim"],
            body.rutinler.calisma, body.rutinler.uyku,
        )
    except Exception as e:  # model yok / tahmin hatası — fark analizi opsiyonel
        logger.warning("Fark analizi atlandı: %s", e)

    prompt_extra = f"{ml_extra}\n{gap_context_paragraph(gap)}" if gap else ml_extra
    prompt = _build_prompt(body.notlar, body.rutinler, ortalamalar, prompt_extra)

    raw, model_name = _generate_raw(prompt)
    if not raw:
        raise HTTPException(status_code=502, detail="Model boş yanıt döndü")

    try:
        ai = _parse_ai_json(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=502,
            detail="Model yanıtı JSON olarak çözülemedi; tekrar deneyin.",
        ) from e

    submission_logged = append_analyze_submission(
        PROJECT_ROOT,
        ortalamalar,
        body.rutinler.calisma,
        body.rutinler.uyku,
    )

    # Giriş yapmış kullanıcı için analizi Raporlar'da göstermek üzere kaydet
    if user is not None:
        genel_ort = int(round((ortalamalar["mat"] + ortalamalar["fiz"] + ortalamalar["kim"]) / 3))
        try:
            db.add(Analysis(
                user_id=user.id,
                mat_avg=ortalamalar["mat"],
                fiz_avg=ortalamalar["fiz"],
                kim_avg=ortalamalar["kim"],
                genel_ort=genel_ort,
                uyku=body.rutinler.uyku,
                calisma=body.rutinler.calisma,
                ai_json=json.dumps(ai, ensure_ascii=False),
            ))
            db.commit()
        except Exception:
            db.rollback()

    return {
        "ai": ai,
        "ortalamalar": ortalamalar,
        "model": model_name,
        "sklearn": sk_meta,
        "gap": gap,
        "submission_logged": submission_logged,
    }


@app.post("/api/learning-path")
def learning_path(body: AnalyzeRequest):
    ortalamalar = {
        "mat": _avg(body.notlar.mat),
        "fiz": _avg(body.notlar.fiz),
        "kim": _avg(body.notlar.kim),
    }
    n, r, o = body.notlar, body.rutinler, ortalamalar
    prompt = f"""
Sen bir eğitim koçusun. Öğrenci bilgileri:
Matematik ortalaması: {o["mat"]}, Fizik ortalaması: {o["fiz"]}, Kimya ortalaması: {o["kim"]}
Günlük uyku: {r.uyku} saat, Günlük ders çalışma: {r.calisma} saat

Bu öğrenci için 4 haftalık kişisel öğrenme yolu oluştur.
Sadece aşağıdaki JSON formatını döndür, başka hiçbir şey yazma:
{{
  "ozet": "Kısa genel değerlendirme (2-3 cümle)",
  "haftalikToplamSaat": <haftalık toplam çalışma saati sayısı>,
  "haftalar": [
    {{
      "hafta": 1,
      "odak": "Bu haftanın odak konusu",
      "gorevler": {{
        "matematik": ["Görev 1", "Görev 2"],
        "fizik": ["Görev 1", "Görev 2"],
        "kimya": ["Görev 1", "Görev 2"]
      }},
      "motivasyon": "Motivasyon cümlesi"
    }}
  ]
}}
"""
    raw, model_name = _generate_raw(prompt)
    if not raw:
        raise HTTPException(status_code=502, detail="Model boş yanıt döndü")

    try:
        plan = _parse_ai_json(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail="Model yanıtı JSON olarak çözülemedi; tekrar deneyin.") from e

    return {"plan": plan}


@app.get("/api/analytics")
def analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Analysis)
        .filter(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.asc())
        .all()
    )
    analyses = []
    for r in rows:
        ai = None
        if r.ai_json:
            try:
                ai = json.loads(r.ai_json)
            except (json.JSONDecodeError, TypeError):
                ai = None
        analyses.append({
            "id": r.id,
            "tarih": r.created_at.strftime("%d.%m.%Y %H:%M") if r.created_at else "",
            "mat": r.mat_avg,
            "fiz": r.fiz_avg,
            "kim": r.kim_avg,
            "genel": r.genel_ort,
            "uyku": r.uyku,
            "calisma": r.calisma,
            "ai": ai,
        })
    return {"analyses": analyses}


# ── HEDEFLER ──────────────────────────────────────────
class GoalCreate(BaseModel):
    baslik: str
    aciklama: str = ""


class GoalUpdate(BaseModel):
    tamamlandi: int = Field(..., ge=0, le=1)


def _goal_dict(g: Goal) -> dict:
    return {
        "id": g.id,
        "baslik": g.baslik,
        "aciklama": g.aciklama or "",
        "tamamlandi": g.tamamlandi,
        "tarih": g.created_at.strftime("%d.%m.%Y") if g.created_at else "",
    }


@app.get("/api/goals")
def list_goals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Goal)
        .filter(Goal.user_id == user.id)
        .order_by(Goal.tamamlandi.asc(), Goal.created_at.desc())
        .all()
    )
    return {"goals": [_goal_dict(g) for g in rows]}


@app.post("/api/goals", status_code=201)
def create_goal(body: GoalCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    baslik = body.baslik.strip()
    if not baslik:
        raise HTTPException(status_code=400, detail="Hedef başlığı boş olamaz")
    goal = Goal(user_id=user.id, baslik=baslik, aciklama=body.aciklama.strip())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _goal_dict(goal)


@app.patch("/api/goals/{goal_id}")
def update_goal(goal_id: int, body: GoalUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Hedef bulunamadı")
    goal.tamamlandi = body.tamamlandi
    db.commit()
    db.refresh(goal)
    return _goal_dict(goal)


@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Hedef bulunamadı")
    db.delete(goal)
    db.commit()
    return {"ok": True}


# --- Rapor Maili (Gmail SMTP) -------------------------------------------------
# /api/analyze'dan tamamen ayrı endpoint: butona basınca tetiklenir, kendi kısa
# timeout'u var (email_sender.SMTP_TIMEOUT) ve threadpool'da çalışır; SMTP takılsa
# bile analiz akışı veya event loop etkilenmez.

class ReportEmailRequest(BaseModel):
    genel_ort: int = Field(..., ge=0, le=100)
    guclu: str = ""
    zayif: str = ""
    ai: dict


# (anahtar öneki, başlık) — ai JSON şeması: matematikDurum / matematikTavsiyeler ...
_REPORT_SECTIONS = [
    ("matematik", "Matematik"),
    ("fizik", "Fizik"),
    ("kimya", "Kimya"),
    ("uyku", "Uyku Düzeni"),
    ("calisma", "Ders Çalışma"),
]


def _build_report_text(body: "ReportEmailRequest") -> str:
    lines = ["EduAI — Akademik Tavsiye Raporu", "",
             f"Genel ortalama: {body.genel_ort}/100"]
    if body.guclu:
        lines.append(f"En güçlü: {body.guclu}")
    if body.zayif:
        lines.append(f"Gelişmeli: {body.zayif}")
    lines.append("")
    for key, title in _REPORT_SECTIONS:
        durum = (body.ai.get(f"{key}Durum") or "").strip()
        tavsiyeler = body.ai.get(f"{key}Tavsiyeler") or []
        lines.append(f"## {title}{' — ' + durum if durum else ''}")
        for t in tavsiyeler:
            lines.append(f"  - {t}")
        lines.append("")
    return "\n".join(lines)


def _build_report_html(body: "ReportEmailRequest") -> str:
    def esc(x: object) -> str:
        return html.escape(str(x))

    sections_html = []
    for key, title in _REPORT_SECTIONS:
        durum = (body.ai.get(f"{key}Durum") or "").strip()
        tavsiyeler = body.ai.get(f"{key}Tavsiyeler") or []
        items = "".join(
            f'<li style="margin:0 0 6px;line-height:1.5;">{esc(t)}</li>'
            for t in tavsiyeler
        )
        sections_html.append(
            f'<div style="margin:0 0 18px;padding:14px 16px;background:#f6fbf9;'
            f'border:1px solid #d6ece2;border-radius:10px;">'
            f'<div style="font-size:15px;font-weight:700;color:#0F6E56;margin-bottom:8px;">'
            f'{esc(title)}{" — " + esc(durum) if durum else ""}</div>'
            f'<ul style="margin:0;padding-left:18px;color:#333;font-size:13px;">{items}</ul>'
            f'</div>'
        )

    return f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:0 auto;padding:24px;color:#1a1a18;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
    <div style="width:34px;height:34px;border-radius:8px;background:#1D9E75;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;">E</div>
    <div style="font-size:18px;font-weight:700;">EduAI — Akademik Tavsiye Raporu</div>
  </div>
  <div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;">
    <div style="flex:1;min-width:120px;background:#e1f5ee;border:1px solid #9fe1cb;border-radius:10px;padding:12px;">
      <div style="font-size:11px;color:#0f6e56;text-transform:uppercase;">Genel ortalama</div>
      <div style="font-size:24px;font-weight:700;color:#0f6e56;">{body.genel_ort}<span style="font-size:13px;color:#888;"> / 100</span></div>
    </div>
    {'<div style="flex:1;min-width:120px;background:#fff;border:1px solid #eee;border-radius:10px;padding:12px;"><div style="font-size:11px;color:#888;text-transform:uppercase;">En güçlü</div><div style="font-size:18px;font-weight:700;color:#0f6e56;">' + esc(body.guclu) + '</div></div>' if body.guclu else ''}
    {'<div style="flex:1;min-width:120px;background:#fff;border:1px solid #eee;border-radius:10px;padding:12px;"><div style="font-size:11px;color:#888;text-transform:uppercase;">Gelişmeli</div><div style="font-size:18px;font-weight:700;color:#185fa5;">' + esc(body.zayif) + '</div></div>' if body.zayif else ''}
  </div>
  {''.join(sections_html)}
  <div style="margin-top:18px;font-size:11px;color:#aaa;text-align:center;">Bu rapor EduAI tarafından otomatik oluşturuldu.</div>
</div>"""


@app.post("/api/send-report")
async def send_report(body: ReportEmailRequest, user: User = Depends(get_current_user)):
    """Analiz raporunu giriş yapan kullanıcının kendi e-postasına gönderir."""
    subject = f"EduAI — Akademik Tavsiye Raporun (Ortalama {body.genel_ort}/100)"
    try:
        await run_in_threadpool(
            send_report_email,
            user.email,
            subject,
            _build_report_html(body),
            _build_report_text(body),
        )
    except EmailConfigError as e:
        # Yapılandırma eksik (local.env'de App Password yok) → 503
        raise HTTPException(status_code=503, detail=str(e))
    except EmailSendError as e:
        # SMTP timeout / auth / bağlantı → 502; demo donmaz, mesaj döner
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True, "to": user.email}


@app.get("/")
def serve_index():
    f = _FRONTEND_DIR / "index.html"
    return FileResponse(f if f.exists() else PROJECT_ROOT / "index.html")


@app.get("/login")
@app.get("/login.html")
def serve_login():
    f = _FRONTEND_DIR / "login.html"
    return FileResponse(f if f.exists() else PROJECT_ROOT / "login.html")


@app.get("/reset")
@app.get("/reset.html")
def serve_reset():
    f = _FRONTEND_DIR / "reset.html"
    return FileResponse(f if f.exists() else PROJECT_ROOT / "reset.html")


@app.get("/style.css")
def serve_css():
    f = _FRONTEND_DIR / "style.css"
    return FileResponse(f if f.exists() else PROJECT_ROOT / "style.css")


_js_dir = _FRONTEND_DIR / "js" if (_FRONTEND_DIR / "js").exists() else PROJECT_ROOT / "js"
app.mount("/js", StaticFiles(directory=str(_js_dir)), name="js")
