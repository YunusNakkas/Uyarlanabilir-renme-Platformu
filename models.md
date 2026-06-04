# `models.py`

SQLAlchemy ORM model tanımları (`backend.database.Base` üzerinden).

## `User` (`users`)

| Kolon | Tip | Not |
| --- | --- | --- |
| `id` | Integer | PK |
| `email` | String | unique, indexed, zorunlu |
| `password_hash` | String | zorunlu |
| `ad` | String | varsayılan boş |
| `soyad` | String | varsayılan boş |
| `created_at` | DateTime | server default `now()` |

## `Goal` (`goals`)

| Kolon | Tip | Not |
| --- | --- | --- |
| `id` | Integer | PK |
| `user_id` | Integer | FK → `users.id` |
| `baslik` | String | zorunlu |
| `aciklama` | String | varsayılan boş |
| `tamamlandi` | Integer | 0=hayır, 1=evet |
| `created_at` | DateTime | server default `now()` |

## `Analysis` (`analyses`)

| Kolon | Tip | Not |
| --- | --- | --- |
| `id` | Integer | PK |
| `user_id` | Integer | FK → `users.id` |
| `mat_avg`, `fiz_avg`, `kim_avg`, `genel_ort` | Integer | zorunlu |
| `uyku`, `calisma` | Float | zorunlu |
| `ai_json` | Text | AI çıktısı (opsiyonel) |
| `created_at` | DateTime | server default `now()` |
