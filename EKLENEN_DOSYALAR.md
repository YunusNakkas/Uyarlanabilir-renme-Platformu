# Eklenen Dosyalar

Bu dökümanda `yunusemrenakkas` dalına son eklenen dosyalar açıklanmaktadır.

## `email_sender.py`

Gmail SMTP üzerinden rapor maili gönderimi yapan modül.

- `/api/analyze` akışından **tamamen bağımsız** çalışır.
- Kısa, kendine ait `SMTP_TIMEOUT` (10 sn) — analiz/Gemini timeout'unu etkilemez; SMTP yavaşlasa bile demo donmaz.
- Hatalar tipli exception olarak yükselir; endpoint yakalayıp kullanıcıya döner.

### Yapı

| Öğe | Açıklama |
| --- | --- |
| `EmailConfigError` | `SMTP_USER` / `SMTP_PASSWORD` eksik veya hatalı. |
| `EmailSendError` | SMTP bağlantısı / kimlik doğrulama / gönderim başarısız. |
| `_config()` | Ortam değişkenlerinden host, port, user, password okur. |
| `send_report_email(...)` | Düz metin + HTML alternatifli tek mail gönderir (senkron). |
| `send_email` | `send_report_email` için genel takma ad (rapor dışı mailler). |

### Kimlik bilgileri (`local.env` — gitignore'lu)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=adresin@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Google App Password (normal şifre DEĞİL)
```

> Not: Gizli bilgi koda gömülü değildir; tümü ortam değişkenlerinden okunur.

## `models.py`

SQLAlchemy ORM model tanımları (`backend.database.Base` üzerinden).

### `User` (`users`)

| Kolon | Tip | Not |
| --- | --- | --- |
| `id` | Integer | PK |
| `email` | String | unique, indexed, zorunlu |
| `password_hash` | String | zorunlu |
| `ad` | String | varsayılan boş |
| `soyad` | String | varsayılan boş |
| `created_at` | DateTime | server default `now()` |

### `Goal` (`goals`)

| Kolon | Tip | Not |
| --- | --- | --- |
| `id` | Integer | PK |
| `user_id` | Integer | FK → `users.id` |
| `baslik` | String | zorunlu |
| `aciklama` | String | varsayılan boş |
| `tamamlandi` | Integer | 0=hayır, 1=evet |
| `created_at` | DateTime | server default `now()` |

### `Analysis` (`analyses`)

| Kolon | Tip | Not |
| --- | --- | --- |
| `id` | Integer | PK |
| `user_id` | Integer | FK → `users.id` |
| `mat_avg`, `fiz_avg`, `kim_avg`, `genel_ort` | Integer | zorunlu |
| `uyku`, `calisma` | Float | zorunlu |
| `ai_json` | Text | AI çıktısı (opsiyonel) |
| `created_at` | DateTime | server default `now()` |
