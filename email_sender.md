# `email_sender.py`

Gmail SMTP üzerinden rapor maili gönderimi yapan modül.

- `/api/analyze` akışından **tamamen bağımsız** çalışır.
- Kısa, kendine ait `SMTP_TIMEOUT` (10 sn) — analiz/Gemini timeout'unu etkilemez; SMTP yavaşlasa bile demo donmaz.
- Hatalar tipli exception olarak yükselir; endpoint yakalayıp kullanıcıya döner.

## Yapı

| Öğe | Açıklama |
| --- | --- |
| `EmailConfigError` | `SMTP_USER` / `SMTP_PASSWORD` eksik veya hatalı. |
| `EmailSendError` | SMTP bağlantısı / kimlik doğrulama / gönderim başarısız. |
| `_config()` | Ortam değişkenlerinden host, port, user, password okur. |
| `send_report_email(...)` | Düz metin + HTML alternatifli tek mail gönderir (senkron). |
| `send_email` | `send_report_email` için genel takma ad (rapor dışı mailler). |

## Kimlik bilgileri (`local.env` — gitignore'lu)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=adresin@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Google App Password (normal şifre DEĞİL)
```

> Not: Gizli bilgi koda gömülü değildir; tümü ortam değişkenlerinden okunur.
