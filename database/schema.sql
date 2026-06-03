-- ============================================================
-- Uyarlanabilir Öğrenme Platformu – Veritabanı Şeması
-- PostgreSQL / SQLite uyumlu
-- ============================================================

-- Kullanıcılar tablosu
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    ad            VARCHAR(100) DEFAULT '',
    soyad         VARCHAR(100) DEFAULT '',
    role          VARCHAR(20)  DEFAULT 'ogrenci',  -- ogrenci | ogretmen | admin
    bio           TEXT         DEFAULT '',
    phone         VARCHAR(30)  DEFAULT '',
    location      VARCHAR(100) DEFAULT '',
    avatar_url    VARCHAR(500),
    is_active     BOOLEAN      DEFAULT TRUE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at    TIMESTAMP WITH TIME ZONE
);

-- Kurslar tablosu
CREATE TABLE IF NOT EXISTS courses (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    description TEXT         DEFAULT '',
    category    VARCHAR(100) DEFAULT '',
    difficulty  VARCHAR(20)  DEFAULT 'baslangic',  -- baslangic | orta | ileri
    created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Kurs kayıt tablosu (öğrenci – kurs ilişkisi)
CREATE TABLE IF NOT EXISTS course_enrollments (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    progress    FLOAT   DEFAULT 0.0,   -- 0.0 – 100.0
    completed   BOOLEAN DEFAULT FALSE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, course_id)
);

-- Quiz tablosu
CREATE TABLE IF NOT EXISTS quizzes (
    id          SERIAL PRIMARY KEY,
    course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title       VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz sonuçları tablosu
CREATE TABLE IF NOT EXISTS quiz_results (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id    INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    score      FLOAT   NOT NULL,     -- 0.0 – 100.0
    duration_s INTEGER DEFAULT 0,   -- Geçen süre (saniye)
    taken_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── İndeksler ───────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_email        ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role         ON users(role);
CREATE INDEX IF NOT EXISTS idx_enrollments_user   ON course_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON course_enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_user  ON quiz_results(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_quiz  ON quiz_results(quiz_id);

-- ─── Örnek Veri ──────────────────────────────────────────────
-- Test admin kullanıcısı (şifre: Admin1234!)
INSERT INTO users (email, password_hash, ad, soyad, role) VALUES
    ('admin@adaptlearn.com', '$2b$12$placeholder_hash', 'Admin', 'User', 'admin')
ON CONFLICT (email) DO NOTHING;
