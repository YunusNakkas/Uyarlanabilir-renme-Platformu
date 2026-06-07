import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Çevresel değişkenlerden veya varsayılan yerel SQLite veritabanından bağlantı dizesini alır.
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL veya MySQL gibi harici veritabanları için motor oluşturma
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Geliştirme ortamı için yerel SQLite veritabanı kurulumu (eduai.db)
    DB_PATH = Path(__file__).parent.parent / "eduai.db"
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False} # SQLite için çoklu thread desteği
    )

# Oturum fabrikası oluşturma
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modellerin türetileceği temel sınıf (ORM Base)
Base = declarative_base()


def get_db():
    """
    FastAPI Dependency: Her HTTP isteği için yeni bir veritabanı 
    oturumu (session) başlatır ve istek bittiğinde otomatik kapatır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
