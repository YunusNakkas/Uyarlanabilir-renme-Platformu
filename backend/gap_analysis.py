"""Fark analizi — iki modeli birleştirmeden, çıktılarını kıyaslayarak içgörü üretir.

İki model AYRI kalır (birleştirmek leakage getirir, bkz. habit_model.py):
  - Not-seviyesi : öğrencinin gerçek notlarından (mevcut DURUM)
  - Alışkanlık-seviyesi : sadece çalışma+uyku saatinden TAHMİN

Aradaki fark asıl bilgidir:
  notlar > alışkanlık  → sonuç iyi ama düzen riskli (sürdürülemez olabilir)
  notlar < alışkanlık  → düzen iyi, henüz nota yansımamış (potansiyel)
  notlar = alışkanlık  → tutarlı

Mesajlar öğrencinin GERÇEK sayılarıyla (çalışma/uyku saati, ortalama) kişiselleştirilir
ve her durumda VERİYE DAYALI somut bir hedef verilir (örn. "Yüksek gruptakiler günde
~4 saat çalışıyor"). Çıktı hem UI'da gösterilir hem Gemini prompt'una bağlam olur.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .habit_model import LEVEL_NAMES, ensure_habit_model, grade_tier_from_avg


def _fmt(saat: float) -> str:
    """Saat değerini sade yazar: 3.0 -> '3', 0.5 -> '0.5'."""
    return f"{saat:g}"


def _verdict_key(grade_tier: int, habit_tier: int) -> str:
    gap = grade_tier - habit_tier
    if gap >= 1:
        return "risk"
    if gap <= -1:
        return "potansiyel"
    return {2: "uyumlu_yuksek", 1: "uyumlu_orta", 0: "uyumlu_dusuk"}[grade_tier]


def _target_tier(key: str, grade_tier: int, habit_tier: int) -> int:
    """Öğrencinin alışkanlık olarak hedefleyeceği seviye (somut hedef bu seviyenin tipik değerleri)."""
    return {
        "risk": grade_tier,            # alışkanlık, notları taşıyacak düzeye çıkmalı
        "potansiyel": habit_tier,      # alışkanlık zaten iyi, korunmalı
        "uyumlu_dusuk": 1,             # bir üst: Orta
        "uyumlu_orta": 2,              # bir üst: Yüksek
        "uyumlu_yuksek": 2,            # mevcut yüksek tempo korunmalı
    }[key]


def _build_message(key: str, study: float, sleep: float, avg: float,
                   grade_name: str, habit_name: str, tgt: dict[str, float]) -> tuple[str, str]:
    """(mesaj, somut_aksiyon) — öğrencinin kendi sayılarıyla kişiselleştirilmiş."""
    s = _fmt(study)
    a = f"{round(avg, 1):g}"
    ts, tu = _fmt(tgt["study"]), _fmt(tgt["sleep"])

    if key == "risk":
        msg = (f"Günde sadece {s} saat çalışıp {a} ortalama tutturmuşsun — şu an yeteneğin "
               f"seni taşıyor. Ama {grade_name} seviyedeki öğrenciler tipik olarak günde ~{ts} "
               f"saat çalışıyor; bu tempo başarını uzun vadede taşımayabilir.")
        act = f"Çalışmayı günde {s} → ~{ts} saate çıkar, uykuyu ~{tu} saatte tut."
    elif key == "potansiyel":
        msg = (f"Günde {s} saat çalışıyorsun — bu {habit_name.lower()} seviyenin düzeni, "
               f"alışkanlıkların iyi. Ama notların ({a} ort.) henüz bunu yansıtmıyor. "
               f"Sorun çalışma süresi değil, büyük ihtimalle yöntem.")
        act = ("Süreyi artırmaya gerek yok; yönteme odaklan — hangi derse ne kadar ayırdığını "
               "ve takıldığın konuları gözden geçir.")
    elif key == "uyumlu_dusuk":
        msg = (f"Hem çalışma düzenin (günde {s} saat) hem notların ({a} ort.) düşük seviyede — "
               f"tutarlı bir tablo ama en hızlı gelişebileceğin nokta tam da burası.")
        act = f"Önce düzeni kur: çalışmayı kademeli ~{ts} saate çıkar, uykuyu ~{tu} saatte sabitle."
    elif key == "uyumlu_orta":
        msg = (f"Çalışman (günde {s} saat) ve notların ({a} ort.) dengeli, orta seviyedesin. "
               f"Bir üst gruba çıkmak gerçekçi bir hedef.")
        act = f"Yüksek gruba geçmek için çalışmayı ~{ts} saate çıkar, uykuyu ~{tu} saatte koru."
    else:  # uyumlu_yuksek
        msg = (f"Hem çalışman (günde {s} saat) hem notların ({a} ort.) yüksek — başarın sağlam "
               f"bir düzene dayanıyor. En sürdürülebilir tablo bu.")
        act = f"Bu tempoyu koru (~{ts} saat çalışma, ~{tu} saat uyku); aşırıya kaçıp tükenme."
    return msg, act


_HEADLINES = {
    "risk": ("⚠️", "Sürdürülebilirlik riski"),
    "potansiyel": ("💡", "Kullanılmayan potansiyel"),
    "uyumlu_dusuk": ("🔴", "Öncelikli gelişim alanı"),
    "uyumlu_orta": ("✅", "Dengeli — bir üst seviye yakın"),
    "uyumlu_yuksek": ("✅", "Tutarlı ve güçlü"),
}


def analyze_gap(
    project_root: Path,
    math: float,
    physical: float,
    chemical: float,
    study_hours: float,
    sleep_hours: float,
) -> dict[str, Any]:
    """İki modeli kıyaslar, kişiselleştirilmiş fark analizi sözlüğü döndürür."""
    bundle = ensure_habit_model(project_root)
    pipe = bundle["pipeline"]
    bins = bundle["grade_bins"]
    benchmarks = bundle.get("tier_benchmarks", {})

    avg = (math + physical + chemical) / 3.0
    grade_tier = grade_tier_from_avg(avg, bins)
    habit_tier = int(pipe.predict([[study_hours, sleep_hours]])[0])

    key = _verdict_key(grade_tier, habit_tier)
    tgt_tier = _target_tier(key, grade_tier, habit_tier)
    tgt = benchmarks.get(tgt_tier, benchmarks.get(2, {"study": 4.0, "sleep": 8.0}))
    icon, headline = _HEADLINES[key]
    message, next_step = _build_message(
        key, study_hours, sleep_hours, avg,
        LEVEL_NAMES[grade_tier], LEVEL_NAMES[habit_tier], tgt,
    )

    return {
        "grade_tier": grade_tier,
        "grade_tier_name": LEVEL_NAMES[grade_tier],
        "habit_tier": habit_tier,
        "habit_tier_name": LEVEL_NAMES[habit_tier],
        "gap": grade_tier - habit_tier,
        "icon": icon,
        "headline": headline,
        "message": message,
        "next_step": next_step,
        "average_score": round(avg, 1),
        "study_hours": study_hours,
        "sleep_hours": sleep_hours,
        "target": tgt,  # {study, sleep} — hedeflenen seviyenin tipik değerleri
    }


def gap_context_paragraph(result: dict[str, Any]) -> str:
    """Gemini prompt'una eklenebilecek tek paragraflık özet."""
    return (
        f"FARK ANALİZİ — Not-seviyesi: {result['grade_tier_name']} (ortalama {result['average_score']}). "
        f"Alışkanlık-seviyesi (yalnız çalışma+uyku saatinden tahmin): {result['habit_tier_name']}. "
        f"Durum: {result['headline']}. {result['message']} Önerilen somut adım: {result['next_step']} "
        f"Tavsiyelerini bu farkı dikkate alarak yaz."
    )
