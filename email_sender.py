"""Gmail SMTP ile rapor maili gönderimi.

Bu modül /api/analyze akışından TAMAMEN bağımsızdır:
- Kısa, kendine ait timeout (SMTP_TIMEOUT) — analiz/Gemini timeout'unu etkilemez.
- Hatalar tipli exception olarak yükselir; endpoint bunları yakalayıp
  kullanıcıya döner, böylece SMTP patlasa bile sayfanın geri kalanı akar.

Kimlik bilgileri local.env'den okunur (gitignore'lu):
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=adresin@gmail.com
    SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Google App Password (normal şifre DEĞİL)
"""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage

SMTP_TIMEOUT = 10  # saniye — kasıtlı kısa; SMTP yavaşsa demo donmasın diye


class EmailConfigError(RuntimeError):
    """SMTP_USER / SMTP_PASSWORD eksik veya hatalı."""


class EmailSendError(RuntimeError):
    """SMTP bağlantısı / kimlik doğrulama / gönderim başarısız."""


def _config() -> tuple[str, int, str, str]:
    host = (os.environ.get("SMTP_HOST") or "smtp.gmail.com").strip()
    try:
        port = int(os.environ.get("SMTP_PORT") or 587)
    except ValueError:
        port = 587
    user = (os.environ.get("SMTP_USER") or "").strip()
    # App Password genelde "xxxx xxxx xxxx xxxx" yapıştırılır; boşlukları temizle
    pwd = (os.environ.get("SMTP_PASSWORD") or "").replace(" ", "").strip()
    if not user or not pwd:
        raise EmailConfigError(
            "SMTP_USER / SMTP_PASSWORD tanımlı değil. "
            "local.env'e Google App Password ekleyin (normal Gmail şifresi çalışmaz)."
        )
    return host, port, user, pwd


def send_report_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """Tek bir mail gönderir. Hata olursa EmailConfigError/EmailSendError yükseltir.

    Senkron (smtplib bloklar) — çağıran taraf run_in_threadpool ile sarmalı.
    """
    host, port, user, pwd = _config()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(text_body)                      # düz metin fallback
    msg.add_alternative(html_body, subtype="html")  # zengin HTML

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT) as server:
            server.starttls(context=context)
            server.login(user, pwd)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise EmailSendError(
            "Gmail kimlik doğrulama başarısız — App Password'ü ve 2FA'yı kontrol edin."
        ) from e
    except (smtplib.SMTPException, OSError) as e:
        # OSError: timeout / bağlantı reddi vb. — demo donmaz, mesajla döneriz
        raise EmailSendError(f"Mail gönderilemedi: {e}") from e


# Genel ad — rapor dışı mailler (ör. şifre doğrulama kodu) için
send_email = send_report_email
