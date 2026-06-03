from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

from backend.database import get_db, engine, Base
from backend import models

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Uyarlanabilir Öğrenme Platformu API",
    description="Makine öğrenimi tabanlı kişiselleştirilmiş öğrenme platformu",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Güvenlik
SECRET_KEY = os.environ.get("SECRET_KEY", "gizli-anahtar-degistir")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 saat

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ─── Pydantic Şemaları ─────────────────────────────────────
class UserCreate(BaseModel):
    ad: str
    soyad: str
    email: EmailStr
    password: str
    role: str = "ogrenci"


class UserUpdate(BaseModel):
    ad: Optional[str] = None
    soyad: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    ad: str
    soyad: str
    email: str
    role: str
    bio: str
    phone: str
    location: str
    avatar_url: Optional[str]
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# ─── Yardımcı Fonksiyonlar ─────────────────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz kimlik bilgileri",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


# ─── Auth Endpoint'leri ────────────────────────────────────
@app.post("/auth/register", response_model=UserOut, status_code=201, tags=["auth"])
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı."""
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı.")
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Şifre en az 8 karakter olmalıdır.")

    user = models.User(
        ad=payload.ad,
        soyad=payload.soyad,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """E-posta + şifre ile giriş, JWT token döner."""
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Hesabınız devre dışı bırakılmış.")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/forgot-password", tags=["auth"])
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Şifre sıfırlama e-postası gönderir."""
    # Gerçek projede e-posta gönderimi burada yapılır
    # Güvenlik için kullanıcı bulunamasa da başarılı döner
    return {"message": "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi."}


# ─── Kullanıcı / Profil Endpoint'leri ─────────────────────
@app.get("/users/me", response_model=UserOut, tags=["users"])
def get_profile(current_user: models.User = Depends(get_current_user)):
    """Giriş yapmış kullanıcının profil bilgilerini döner."""
    return current_user


@app.put("/users/me", response_model=UserOut, tags=["users"])
def update_profile(
    payload: UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Profil bilgilerini günceller."""
    if payload.email and payload.email != current_user.email:
        existing = db.query(models.User).filter(models.User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu e-posta zaten kullanımda.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@app.put("/users/me/password", tags=["users"])
def change_password(
    payload: PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Şifre değiştirme."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı.")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=422, detail="Yeni şifre en az 8 karakter olmalıdır.")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Şifre başarıyla güncellendi."}


@app.post("/users/me/avatar", tags=["users"])
def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Avatar yükleme (dosya adını kaydeder; production'da S3/CDN'e yüklenecek)."""
    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if avatar.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya türü.")

    # Gerçek projede: dosyayı S3'e yükle, URL'i kaydet
    current_user.avatar_url = f"/avatars/{current_user.id}_{avatar.filename}"
    db.commit()
    return {"avatar_url": current_user.avatar_url}


@app.delete("/users/me", tags=["users"])
def delete_account(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hesabı kalıcı olarak siler."""
    db.delete(current_user)
    db.commit()
    return {"message": "Hesabınız başarıyla silindi."}


# ─── Sağlık Kontrolü ──────────────────────────────────────
@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "service": "Uyarlanabilir Öğrenme Platformu API"}
