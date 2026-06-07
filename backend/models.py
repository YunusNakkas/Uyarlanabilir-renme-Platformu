# Author: Fatma Türkmen - Veritabanı Modelleri ve İlişki Tanımları
from sqlalchemy import (
    Column, Float, ForeignKey, Integer, String,
    DateTime, Boolean, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import enum


class UserRole(str, enum.Enum):
    ogrenci = "ogrenci"
    ogretmen = "ogretmen"
    admin = "admin"


class User(Base):
    """Kullanıcı modeli – öğrenci, öğretmen ve admin rolleri desteklenir."""
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    ad            = Column(String, default="")
    soyad         = Column(String, default="")
    role          = Column(String, default="ogrenci")  # UserRole enum
    bio           = Column(Text, default="")
    phone         = Column(String, default="")
    location      = Column(String, default="")
    avatar_url    = Column(String, nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    courses       = relationship("CourseEnrollment", back_populates="user", cascade="all, delete-orphan")
    quiz_results  = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"


class Course(Base):
    """Ders/Kurs modeli."""
    __tablename__ = "courses"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String, nullable=False)
    description = Column(Text, default="")
    category    = Column(String, default="")
    difficulty  = Column(String, default="baslangic")  # baslangic, orta, ileri
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    quizzes     = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course id={self.id} title={self.title}>"


class CourseEnrollment(Base):
    """Öğrenci – Kurs kayıt ilişkisi."""
    __tablename__ = "course_enrollments"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id   = Column(Integer, ForeignKey("courses.id"), nullable=False)
    progress    = Column(Float, default=0.0)       # 0.0 – 100.0
    completed   = Column(Boolean, default=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    user   = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="enrollments")


class Quiz(Base):
    """Quiz / Test modeli."""
    __tablename__ = "quizzes"

    id          = Column(Integer, primary_key=True, index=True)
    course_id   = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title       = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    course      = relationship("Course", back_populates="quizzes")
    results     = relationship("QuizResult", back_populates="quiz", cascade="all, delete-orphan")


class QuizResult(Base):
    """Öğrenci quiz sonuçları."""
    __tablename__ = "quiz_results"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id    = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score      = Column(Float, nullable=False)      # 0.0 – 100.0
    duration_s = Column(Integer, default=0)         # Süre (saniye)
    taken_at   = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz", back_populates="results")
