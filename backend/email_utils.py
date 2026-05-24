import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .logger import logger


def send_reset_email(to_email: str, reset_url: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()

    if not smtp_user or not smtp_pass:
        raise RuntimeError("SMTP_USER ve SMTP_PASSWORD local.env dosyasında tanımlanmalı")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "EduAI - Şifre Sıfırlama"
    msg["From"] = f"EduAI <{smtp_user}>"
    msg["To"] = to_email

    text_body = (
        f"Merhaba,\n\n"
        f"Şifre sıfırlama talebinde bulundunuz.\n"
        f"Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n\n"
        f"{reset_url}\n\n"
        f"Bu bağlantı 1 saat geçerlidir.\n"
        f"Talebi siz yapmadıysanız bu e-postayı görmezden gelin.\n\n"
        f"EduAI Ekibi"
    )

    html_body = f"""<!DOCTYPE html>
<html lang="tr"><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f3;margin:0;padding:40px 16px;">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:16px;padding:40px;border:1px solid rgba(0,0,0,0.08);">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:28px;">
    <div style="width:24px;height:24px;border-radius:7px;background:#1D9E75;"></div>
    <span style="font-size:18px;font-weight:700;color:#1a1a18;">EduAI</span>
  </div>
  <h2 style="font-size:20px;font-weight:600;color:#1a1a18;margin-bottom:12px;">Şifre Sıfırlama</h2>
  <p style="color:#5f5e5a;font-size:14px;line-height:1.6;margin-bottom:24px;">
    Şifre sıfırlama talebinde bulundunuz. Aşağıdaki butona tıklayarak yeni şifrenizi belirleyebilirsiniz.
  </p>
  <a href="{reset_url}" style="display:inline-block;background:#1D9E75;color:#fff;text-decoration:none;border-radius:8px;padding:12px 28px;font-size:14px;font-weight:600;">
    Şifremi Sıfırla
  </a>
  <p style="color:#888780;font-size:12px;margin-top:24px;line-height:1.5;">
    Bu bağlantı <strong>1 saat</strong> geçerlidir.<br>
    Talebi siz yapmadıysanız bu e-postayı güvenle silebilirsiniz.
  </p>
</div>
</body></html>"""

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())

    logger.info(f"Şifre sıfırlama e-postası gönderildi: {to_email}")
