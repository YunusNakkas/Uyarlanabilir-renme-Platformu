from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    ad = Column(String, default="")
    soyad = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    baslik = Column(String, nullable=False)
    aciklama = Column(String, default="")
    tamamlandi = Column(Integer, default=0)  # 0=hayır, 1=evet
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mat_avg = Column(Integer, nullable=False)
    fiz_avg = Column(Integer, nullable=False)
    kim_avg = Column(Integer, nullable=False)
    genel_ort = Column(Integer, nullable=False)
    uyku = Column(Float, nullable=False)
    calisma = Column(Float, nullable=False)
    ai_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Integer, default=0)  # 0=hayır, 1=evet
    created_at = Column(DateTime(timezone=True), server_default=func.now())
