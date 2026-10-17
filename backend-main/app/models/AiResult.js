// app/models/AiResult.js
const mongoose = require('mongoose');

const AiResultSchema = new mongoose.Schema({
  type: { type: String, required: true, enum: ['불', '연기'] },
  confidence: { type: Number, required: true, min: 0, max: 100 }, // 퍼센트 (예: 88.2)
  location: { type: String, required: true },   // 예: "대구가톨릭대학교 정문 앞"
  cameraId: { type: String },                    // 예: "cam-01"
  latitude: { type: Number },
  longitude: { type: Number },
  bbox: { type: [Number] },                      // [x1, y1, x2, y2] (픽셀, 원본 프레임 기준)
  imageUrl: { type: String },                    // 감지 순간 스냅샷 (/snapshots/xxx.jpg)
  streamUrl: { type: String },                   // 공공 CCTV 등 http(s) 실시간 영상 주소 (있을 때만)
  timestamp: { type: Date, default: Date.now, index: true },
});

mongoose.model('AiResult', AiResultSchema);
