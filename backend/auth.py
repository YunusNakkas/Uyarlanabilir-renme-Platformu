import os
import random
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from .database import get_db
from .email_sender import EmailConfigError, EmailSendError, send_email
from .models import Analysis, Goal, User

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "eduai-fallback-key-set-in-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

# Şifre değiştirme doğrulama kodu (OTP) — tek süreçlik local demo için bellek içi store.
# {email: (kod, son_geçerlilik_zamanı)}
OTP_TTL_SECONDS = 300  # 5 dakika
_password_otps: dict[str, tuple[str, float]] = {}


def _issue_otp(email: str) -> str:
    code = f"{random.randint(0, 999999):06d}"
    _password_otps[email] = (code, time.time() + OTP_TTL_SECONDS)
    return code


def _verify_otp(email: str, code: str) -> bool:
    item = _password_otps.get(email)
    if not item:
        return False
    saved, expires = item
    if time.time() > expires:
        _password_otps.pop(email, None)
        return False
    if saved != (code or "").strip():
        return False
    _password_otps.pop(email, None)  # tek kullanımlık
    return True


def _send_welcome_email(email: str) -> None:
    """Kayıt sonrası hoş geldin maili. Hata olursa yutulur — kayıt asla başarısız olmaz."""
    subject = "EduAI'ya Hoş Geldin 🎓"
    text = (
        "EduAI'ya hoş geldin!\n\n"
        "Hesabın başarıyla oluşturuldu. Artık not ve rutinlerini girerek "
        "yapay zeka destekli kişisel akademik tavsiyeler alabilirsin.\n\n"
        "Başarılar dileriz,\nEduAI Ekibi"
    )
    html = """\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:0 auto;padding:24px;color:#1a1a18;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
    <div style="width:36px;height:36px;border-radius:8px;background:#1D9E75;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;">E</div>
    <div style="font-size:18px;font-weight:700;">EduAI'ya Hoş Geldin 🎓</div>
  </div>
  <p style="font-size:14px;color:#555;line-height:1.6;">Hesabın başarıyla oluşturuldu. Artık math/fizik/kimya notlarını ve günlük uyku/çalışma saatlerini girerek <b>yapay zeka destekli kişisel akademik tavsiyeler</b> alabilirsin.</p>
  <div style="margin:18px 0;padding:14px 16px;background:#e1f5ee;border:1px solid #9fe1cb;border-radius:10px;font-size:13px;color:#0f6e56;">İlk analizini yapmak için giriş yap ve notlarını gir — yapay zeka koçun hazır.</div>
  <p style="font-size:12px;color:#888;">Başarılar dileriz,<br>EduAI Ekibi</p>
</div>"""
    try:
        send_email(email, subject, html, text)
    except (EmailConfigError, EmailSendError):
        pass  # mail gitmese de kayıt geçerli


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    # Şema-opsiyonel; gerçek zorunluluk sunucuda _verify_otp ile sağlanır (boş kod → 400)
    code: str = ""


class RequestRegisterCodeRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _truncate_password(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def _hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_password(password))


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate_password(plain), hashed)


def _create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı")
    return user


@router.post("/request-register-code")
@limiter.limit("3/minute")
def request_register_code(request: Request, body: RequestRegisterCodeRequest, db: Session = Depends(get_db)):
    """Kayıt için e-postaya 6 haneli doğrulama kodu gönderir."""
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
    code = _issue_otp(body.email)
    subject = "EduAI — E-posta Doğrulama Kodu"
    text = (
        f"EduAI kayıt doğrulama kodun: {code}\n"
        f"Kod {OTP_TTL_SECONDS // 60} dakika geçerlidir. Kaydı sen başlatmadıysan dikkate alma."
    )
    html = f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:440px;margin:0 auto;padding:24px;color:#1a1a18;">
  <div style="font-size:16px;font-weight:700;margin-bottom:12px;">EduAI — E-posta Doğrulama</div>
  <p style="font-size:14px;color:#555;">Kaydını tamamlamak için aşağıdaki kodu uygulamaya gir:</p>
  <div style="font-size:32px;font-weight:800;letter-spacing:8px;color:#1D9E75;background:#e1f5ee;border:1px solid #9fe1cb;border-radius:10px;padding:16px;text-align:center;margin:16px 0;">{code}</div>
  <p style="font-size:12px;color:#888;">Kod {OTP_TTL_SECONDS // 60} dakika geçerlidir. Bu işlemi sen başlatmadıysan bu maili dikkate alma.</p>
</div>"""
    try:
        send_email(body.email, subject, html, text)
    except EmailConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EmailSendError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı")
    if not _verify_otp(body.email, body.code):
        raise HTTPException(status_code=400, detail="Doğrulama kodu hatalı veya süresi dolmuş")
    user = User(email=body.email, password_hash=_hash_password(body.password))
    db.add(user)
    db.commit()
    _send_welcome_email(body.email)  # hata yutulur, kayıt etkilenmez
    token = _create_token(body.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not _verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")
    token = _create_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "ad": current_user.ad or "",
        "soyad": current_user.soyad or "",
        "created_at": current_user.created_at,
    }


@router.delete("/account")
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Giriş yapan kullanıcının hesabını ve tüm verilerini siler (geri alınamaz)."""
    db.query(Goal).filter(Goal.user_id == current_user.id).delete()
    db.query(Analysis).filter(Analysis.user_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()
    return {"ok": True}


class UpdateProfileRequest(BaseModel):
    ad: str = ""
    soyad: str = ""


@router.patch("/profile")
def update_profile(body: UpdateProfileRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.ad = body.ad.strip()
    current_user.soyad = body.soyad.strip()
    db.add(current_user)
    db.commit()
    return {"ok": True, "ad": current_user.ad, "soyad": current_user.soyad}


@router.post("/request-password-code")
@limiter.limit("3/minute")
def request_password_code(request: Request, current_user: User = Depends(get_current_user)):
    """Şifre değiştirme için giriş yapan kullanıcının e-postasına 6 haneli kod gönderir."""
    code = _issue_otp(current_user.email)
    subject = "EduAI — Şifre Değiştirme Kodu"
    text = (
        f"Şifre değiştirme doğrulama kodun: {code}\n"
        f"Kod {OTP_TTL_SECONDS // 60} dakika geçerlidir. Bu işlemi sen başlatmadıysan dikkate alma."
    )
    html = f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:440px;margin:0 auto;padding:24px;color:#1a1a18;">
  <div style="font-size:16px;font-weight:700;margin-bottom:12px;">EduAI — Şifre Değiştirme Kodu</div>
  <p style="font-size:14px;color:#555;">Şifreni değiştirmek için aşağıdaki kodu uygulamaya gir:</p>
  <div style="font-size:32px;font-weight:800;letter-spacing:8px;color:#1D9E75;background:#e1f5ee;border:1px solid #9fe1cb;border-radius:10px;padding:16px;text-align:center;margin:16px 0;">{code}</div>
  <p style="font-size:12px;color:#888;">Kod {OTP_TTL_SECONDS // 60} dakika geçerlidir. Bu işlemi sen başlatmadıysan bu maili dikkate alma.</p>
</div>"""
    try:
        send_email(current_user.email, subject, html, text)
    except EmailConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EmailSendError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    code: str = ""  # sunucuda _verify_otp ile zorunlu


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı")
    if not _verify_otp(current_user.email, body.code):
        raise HTTPException(status_code=400, detail="Doğrulama kodu hatalı veya süresi dolmuş")
    current_user.password_hash = _hash_password(body.new_password)
    db.add(current_user)
    db.commit()
    return {"ok": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/check-email")
@limiter.limit("10/minute")
def check_email(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == body.email).first() is not None
    return {"exists": exists}


class RequestResetCodeRequest(BaseModel):
    email: EmailStr


@router.post("/request-reset-code")
@limiter.limit("3/minute")
def request_reset_code(request: Request, body: RequestResetCodeRequest, db: Session = Depends(get_db)):
    """Şifre sıfırlama için e-postaya 6 haneli kod gönderir (kullanıcı varsa)."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        # Hesap sıralamasını sızdırmamak için yine ok dön; mail göndermeyiz
        return {"ok": True}
    code = _issue_otp(body.email)
    subject = "EduAI — Şifre Sıfırlama Kodu"
    text = (
        f"Şifre sıfırlama doğrulama kodun: {code}\n"
        f"Kod {OTP_TTL_SECONDS // 60} dakika geçerlidir. Bu işlemi sen başlatmadıysan dikkate alma."
    )
    html = f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:440px;margin:0 auto;padding:24px;color:#1a1a18;">
  <div style="font-size:16px;font-weight:700;margin-bottom:12px;">EduAI — Şifre Sıfırlama Kodu</div>
  <p style="font-size:14px;color:#555;">Şifreni sıfırlamak için aşağıdaki kodu uygulamaya gir:</p>
  <div style="font-size:32px;font-weight:800;letter-spacing:8px;color:#1D9E75;background:#e1f5ee;border:1px solid #9fe1cb;border-radius:10px;padding:16px;text-align:center;margin:16px 0;">{code}</div>
  <p style="font-size:12px;color:#888;">Kod {OTP_TTL_SECONDS // 60} dakika geçerlidir. Bu işlemi sen başlatmadıysan bu maili dikkate alma.</p>
</div>"""
    try:
        send_email(body.email, subject, html, text)
    except EmailConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except EmailSendError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


class DirectResetRequest(BaseModel):
    email: EmailStr
    new_password: str
    code: str = ""  # sunucuda _verify_otp ile zorunlu


@router.post("/reset-password-direct")
@limiter.limit("5/minute")
def reset_password_direct(request: Request, body: DirectResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Bu e-posta ile kayıtlı kullanıcı bulunamadı")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı")
    if not _verify_otp(body.email, body.code):
        raise HTTPException(status_code=400, detail="Doğrulama kodu hatalı veya süresi dolmuş")
    user.password_hash = _hash_password(body.new_password)
    db.add(user)
    db.commit()
    return {"ok": True, "message": "Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz."}
