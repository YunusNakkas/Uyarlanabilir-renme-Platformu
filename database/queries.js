const mongoose = require("mongoose");

const userSchema = new mongoose.Schema(
  {
    name: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    role: { type: String, enum: ["student", "teacher"], default: "student" },
    learningStyle: {
      type: String,
      enum: ["visual", "auditory", "reading"],
      default: "visual",
    },
  },
  { timestamps: true }
);

const contentSchema = new mongoose.Schema(
  {
    title: { type: String, required: true },
    type: { type: String, enum: ["text", "video", "quiz"], required: true },
    difficultyLevel: { type: Number, min: 1, max: 5, required: true },
    subject: { type: String, required: true },
    createdBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  },
  { timestamps: true }
);

const performanceSchema = new mongoose.Schema(
  {
    student: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },
    content: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Content",
      required: true,
    },
    completionRate: { type: Number, min: 0, max: 100, default: 0 },
    quizScore: { type: Number, min: 0, max: 100, default: 0 },
    timeSpent: { type: Number, default: 0 },
    completedAt: { type: Date },
  },
  { timestamps: true }
);

userSchema.index({ email: 1 });
performanceSchema.index({ student: 1 });
contentSchema.index({ type: 1, difficultyLevel: 1 });
performanceSchema.index({ completionRate: -1 });

const User = mongoose.model("User", userSchema);
const Content = mongoose.model("Content", contentSchema);
const Performance = mongoose.model("Performance", performanceSchema);

const getStudentPerformance = async (studentId) => {
  return await Performance.find({ student: studentId })
    .populate("content", "title type difficultyLevel")
    .select("completionRate quizScore timeSpent completedAt")
    .sort({ createdAt: -1 })
    .lean();
};

const getAverageScore = async (studentId) => {
  const result = await Performance.aggregate([
    { $match: { student: new mongoose.Types.ObjectId(studentId) } },
    {
      $group: {
        _id: "$student",
        averageScore: { $avg: "$quizScore" },
        averageCompletion: { $avg: "$completionRate" },
        totalTimeSpent: { $sum: "$timeSpent" },
        totalContents: { $count: {} },
      },
    },
  ]);
  return result[0] || null;
};

const recommendContent = async (studentId) => {
  const stats = await getAverageScore(studentId);
  if (!stats) return [];

  const avgScore = stats.averageScore || 0;

  let difficultyRange;
  if (avgScore < 50) {
    difficultyRange = { $lte: 2 };
  } else if (avgScore < 75) {
    difficultyRange = { $eq: 3 };
  } else {
    difficultyRange = { $gte: 4 };
  }

  const seen = await Performance.find({ student: studentId }).select("content");
  const seenIds = seen.map((p) => p.content);

  return await Content.find({
    difficultyLevel: difficultyRange,
    _id: { $nin: seenIds },
  })
    .limit(5)
    .lean();
};

const getPlatformStats = async () => {
  return await Performance.aggregate([
    {
      $group: {
        _id: null,
        totalStudents: { $addToSet: "$student" },
        avgPlatformScore: { $avg: "$quizScore" },
        avgCompletion: { $avg: "$completionRate" },
      },
    },
    {
      $project: {
        totalStudents: { $size: "$totalStudents" },
        avgPlatformScore: { $round: ["$avgPlatformScore", 1] },
        avgCompletion: { $round: ["$avgCompletion", 1] },
      },
    },
  ]);
};

module.exports = {
  User,
  Content,
  Performance,
  getStudentPerformance,
  getAverageScore,
  recommendContent,
  getPlatformStats,
};
