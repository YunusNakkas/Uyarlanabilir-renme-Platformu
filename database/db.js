const mongoose = require("mongoose");

const MONGO_URI =
  process.env.MONGO_URI || "mongodb://localhost:27017/ogrenme_platformu";

const options = {
  useNewUrlParser: true,
  useUnifiedTopology: true,
};

const connectDB = async () => {
  try {
    await mongoose.connect(MONGO_URI, options);
    console.log("✅ MongoDB bağlantısı başarılı!");
    console.log(`📦 Veritabanı: ogrenme_platformu`);
  } catch (error) {
    console.error("❌ MongoDB bağlantı hatası:", error.message);
    process.exit(1);
  }
};

mongoose.connection.on("disconnected", () => {
  console.warn("⚠️ MongoDB bağlantısı koptu. Yeniden bağlanılıyor...");
});

module.exports = connectDB;
