// app/models/AIErrorLog.js
const mongoose = require('mongoose');

const AiErrorLogSchema = new mongoose.Schema({
  errorType: { type: String, required: true }, // 예: 'CAMERA_DISCONNECTED'
  message: { type: String },
  location: { type: String },
  cameraId: { type: String },
  rawData: { type: Object },
  timestamp: { type: Date, default: Date.now, index: true },
});

mongoose.model('AiErrorLog', AiErrorLogSchema);
