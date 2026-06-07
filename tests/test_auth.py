import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db

# Testler için geçici bir bellek-içi (in-memory) SQLite veritabanı kurulumu yapıyoruz.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope="function")
def db():
    """Her test fonksiyonu için yeni bir temiz veritabanı oturumu oluşturur."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """get_db bağımlılığını mock veritabanıyla değiştirerek TestClient sunar."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_register_user(client):
    """Yeni kullanıcı kaydını doğrular."""
    response = client.post(
        "/auth/register",
        json={
            "ad": "Test",
            "soyad": "Kullanici",
            "email": "test@edu.com",
            "password": "sifre123_guclu",
            "role": "ogrenci"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@edu.com"
    assert "id" in data


def test_register_duplicate_email(client):
    """Aynı e-posta adresiyle mükerrer kayıt hatasını doğrular."""
    # İlk kayıt
    client.post(
        "/auth/register",
        json={
            "ad": "Test1",
            "soyad": "Kullanici",
            "email": "ayni@edu.com",
            "password": "sifre123_guclu",
            "role": "ogrenci"
        }
    )
    # İkinci kayıt (aynı e-posta)
    response = client.post(
        "/auth/register",
        json={
            "ad": "Test2",
            "soyad": "Kullanici",
            "email": "ayni@edu.com",
            "password": "sifre123_guclu",
            "role": "ogretmen"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Bu e-posta adresi zaten kayıtlı."


def test_login_success(client):
    """Başarılı giriş işlemini ve JWT token dönüşünü doğrular."""
    # Önce kullanıcı oluştur
    client.post(
        "/auth/register",
        json={
            "ad": "Login",
            "soyad": "Test",
            "email": "login@edu.com",
            "password": "sifre123_guclu",
            "role": "ogrenci"
        }
    )
    # Giriş yapmayı dene
    response = client.post(
        "/auth/login",
        data={
            "username": "login@edu.com",
            "password": "sifre123_guclu"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Hatalı şifre girildiğinde yetkilendirme hatası verilmesini doğrular."""
    client.post(
        "/auth/register",
        json={
            "ad": "Login",
            "soyad": "Test",
            "email": "wrongpass@edu.com",
            "password": "sifre123_guclu",
            "role": "ogrenci"
        }
    )
    response = client.post(
        "/auth/login",
        data={
            "username": "wrongpass@edu.com",
            "password": "yanlis_sifre"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "E-posta veya şifre hatalı."
