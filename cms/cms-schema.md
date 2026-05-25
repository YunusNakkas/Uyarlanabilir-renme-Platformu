# 🗃️ İçerik Yönetim Sistemi (CMS) Veritabanı Şeması

---

## 1. 📋 Koleksiyonlar

### 1.1 İçerikler (contents)

İçerik oluşturma ve yönetim sistemi için ana koleksiyon.

const contentSchema = new mongoose.Schema(
  {
    title: { type: String, required: true },
    description: { type: String },
    type: {
      type: String,
      enum: ["text", "video", "quiz"],
      required: true
    },
    difficultyLevel: { type: Number, min: 1, max: 5 },
    subject: { type: String, required: true },
    tags: [{ type: String }],
    duration: { type: Number },
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
    isPublished: { type: Boolean, default: false },
    viewCount: { type: Number, default: 0 },
  },
  { timestamps: true }
);

### 1.2 Metin İçerikleri (text_contents)

const textContentSchema = new mongoose.Schema({
  content: { type: mongoose.Schema.Types.ObjectId, ref: "Content" },
  body: { type: String, required: true },
  readingTime: { type: Number },
  format: { type: String, enum: ["markdown", "html"], default: "markdown" },
});

### 1.3 Video İçerikleri (video_contents)

const videoContentSchema = new mongoose.Schema({
  content: { type: mongoose.Schema.Types.ObjectId, ref: "Content" },
  videoUrl: { type: String, required: true },
  thumbnailUrl: { type: String },
  duration: { type: Number, required: true },
  subtitles: { type: Boolean, default: false },
});

### 1.4 Sınavlar (quizzes)

const quizSchema = new mongoose.Schema({
  content: { type: mongoose.Schema.Types.ObjectId, ref: "Content" },
  questions: [
    {
      questionText: { type: String, required: true },
      options: [{ type: String }],
      correctAnswer: { type: Number, required: true },
      points: { type: Number, default: 10 },
    }
  ],
  passingScore: { type: Number, default: 60 },
  timeLimit: { type: Number },
});

### 1.5 Meta Veriler (content_meta)

const contentMetaSchema = new mongoose.Schema({
  content: { type: mongoose.Schema.Types.ObjectId, ref: "Content" },
  language: { type: String, default: "tr" },
  targetAudience: { type: String },
  prerequisites: [{ type: mongoose.Schema.Types.ObjectId, ref: "Content" }],
  relatedContents: [{ type: mongoose.Schema.Types.ObjectId, ref: "Content" }],
});
## 2. ⚡ İndeksleme Stratejileri

contentSchema.index({ subject: 1, type: 1 });
contentSchema.index({ difficultyLevel: 1 });
contentSchema.index({ isPublished: 1 });
contentSchema.index({ tags: 1 });
contentSchema.index({ viewCount: -1 });

---

## 3. 🔗 Koleksiyonlar Arası İlişkiler

contents
   ├── text_contents   (1'e 1)
   ├── video_contents  (1'e 1)
   ├── quizzes         (1'e 1)
   └── content_meta    (1'e 1)

users
   └── contents (1'e çok)

contents
   └── performances (1'e çok)

---

## 4. 📊 Performans ve Ölçeklenebilirlik

- İndeksleme ile sık kullanılan sorgular hızlandırıldı
- Ayrı koleksiyonlar ile içerik türleri yönetilebilir hale getirildi
- ref kullanımı ile ilişkisel veri yapısı kuruldu
- timestamps ile içerik geçmişi takip edilebilir
- isPublished alanı ile taslak/yayın sistemi kuruldu
