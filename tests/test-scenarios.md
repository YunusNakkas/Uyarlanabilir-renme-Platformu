# 🧪 Otomatik Test Senaryoları

**Sorumlu:** Melike Keke  
**Görev:** Otomatik Test Senaryoları Geliştirme  
**Tarih:** 8 Mayıs 2026  
**Teknoloji:** Jest (Node.js)

---

## 1. Kullanıcı Kayıt ve Giriş Testleri

### Test 1.1 — Başarılı Kullanıcı Kaydı
```js
test('Yeni kullanıcı başarıyla kaydolabilmeli', async () => {
  const response = await request(app)
    .post('/api/auth/register')
    .send({
      name: 'Test Kullanıcı',
      email: 'test@example.com',
      password: '123456',
      role: 'student'
    });

  expect(response.status).toBe(201);
  expect(response.body).toHaveProperty('token');
});
```

### Test 1.2 — Aynı Email ile Tekrar Kayıt
```js
test('Aynı email ile tekrar kayıt olunamamalı', async () => {
  const response = await request(app)
    .post('/api/auth/register')
    .send({
      name: 'Test Kullanıcı',
      email: 'test@example.com',
      password: '123456',
    });

  expect(response.status).toBe(400);
  expect(response.body.message).toBe('Bu email zaten kayıtlı');
});
```

### Test 1.3 — Başarılı Giriş
```js
test('Kayıtlı kullanıcı giriş yapabilmeli', async () => {
  const response = await request(app)
    .post('/api/auth/login')
    .send({
      email: 'test@example.com',
      password: '123456',
    });

  expect(response.status).toBe(200);
  expect(response.body).toHaveProperty('token');
});
```

### Test 1.4 — Yanlış Şifre ile Giriş
```js
test('Yanlış şifre ile giriş yapılamamalı', async () => {
  const response = await request(app)
    .post('/api/auth/login')
    .send({
      email: 'test@example.com',
      password: 'yanlis_sifre',
    });

  expect(response.status).toBe(401);
  expect(response.body.message).toBe('Şifre hatalı');
});
```

---

## 2. İçerik Yönetim Testleri

### Test 2.1 — İçerik Oluşturma
```js
test('Öğretmen yeni içerik oluşturabilmeli', async () => {
  const response = await request(app)
    .post('/api/content')
    .set('Authorization', `Bearer ${teacherToken}`)
    .send({
      title: 'JavaScript Temelleri',
      type: 'video',
      difficultyLevel: 2,
      subject: 'Programlama'
    });

  expect(response.status).toBe(201);
  expect(response.body.title).toBe('JavaScript Temelleri');
});
```

### Test 2.2 — İçerik Listeleme
```js
test('Tüm içerikler listelenebilmeli', async () => {
  const response = await request(app)
    .get('/api/content')
    .set('Authorization', `Bearer ${studentToken}`);

  expect(response.status).toBe(200);
  expect(Array.isArray(response.body)).toBe(true);
});
```

---

## 3. Performans ve Öneri Testleri

### Test 3.1 — Öğrenci Performansı Kaydetme
```js
test('Öğrenci performansı kaydedilebilmeli', async () => {
  const response = await request(app)
    .post('/api/performance')
    .set('Authorization', `Bearer ${studentToken}`)
    .send({
      contentId: 'icerik_id',
      completionRate: 85,
      quizScore: 90,
      timeSpent: 1200
    });

  expect(response.status).toBe(201);
  expect(response.body.quizScore).toBe(90);
});
```

### Test 3.2 — Kişiselleştirilmiş İçerik Önerisi
```js
test('Öğrenciye uygun zorlukta içerik önerilmeli', async () => {
  const response = await request(app)
    .get('/api/recommend')
    .set('Authorization', `Bearer ${studentToken}`);

  expect(response.status).toBe(200);
  expect(response.body.length).toBeGreaterThan(0);
});
```

---

## 4. 📊 Test Sonuçları

| Test | Durum |
|------|-------|
| Başarılı kullanıcı kaydı | ✅ Geçti |
| Aynı email tekrar kayıt | ✅ Geçti |
| Başarılı giriş | ✅ Geçti |
| Yanlış şifre girişi | ✅ Geçti |
| İçerik oluşturma | ✅ Geçti |
| İçerik listeleme | ✅ Geçti |
| Performans kaydetme | ✅ Geçti |
| İçerik önerisi | ✅ Geçti |

**Toplam: 8/8 test başarılı ✅**
