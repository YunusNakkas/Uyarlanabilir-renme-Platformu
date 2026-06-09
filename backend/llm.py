"""LLM sağlayıcı soyutlaması — Groq (OpenAI uyumlu) desteği.

Gemini kotası dolduğunda Groq'a geçilebilir. Sağlayıcı seçimi env ile:
    LLM_PROVIDER=groq        # veya gemini (boşsa GROQ_API_KEY varsa groq)
    GROQ_API_KEY=...         # console.groq.com/keys (ücretsiz)
    GROQ_MODEL=llama-3.3-70b-versatile   # opsiyonel

Yeni bağımlılık yok — stdlib urllib ile HTTP. Çağrı senkron, kendi timeout'u var.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"
LLM_TIMEOUT = 60  # saniye


class LLMError(RuntimeError):
    """Groq çağrısı başarısız (config, HTTP, parse)."""


def use_groq() -> bool:
    """Groq mı kullanılacak? LLM_PROVIDER açıkça belirtilmişse ona uy,
    yoksa GROQ_API_KEY varsa Groq'a geç."""
    provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
    if provider:
        return provider == "groq"
    return bool((os.environ.get("GROQ_API_KEY") or "").strip())


def groq_generate(prompt: str) -> tuple[str, str]:
    """Groq'tan JSON metni üretir. (ham_metin, model_etiketi) döner; hata→LLMError."""
    key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not key:
        raise LLMError(
            "GROQ_API_KEY tanımlı değil. local.env'e ekleyin (console.groq.com/keys — ücretsiz)."
        )
    model = (os.environ.get("GROQ_MODEL") or GROQ_DEFAULT_MODEL).strip()

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system",
             "content": "Sadece geçerli, hatasız JSON döndür. Markdown, kod bloğu veya ek metin yazma."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            # Cloudflare, varsayılan "Python-urllib" UA'sını 1010 ile bloklar — normal UA ver
            "User-Agent": "EduAI/1.0 (+https://localhost)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise LLMError(f"Groq {e.code}: {body}") from e
    except Exception as e:  # timeout / bağlantı
        raise LLMError(f"Groq bağlantı hatası: {e}") from e

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"Groq beklenmeyen yanıt biçimi: {str(data)[:200]}") from e

    return text or "", f"groq:{model}"
