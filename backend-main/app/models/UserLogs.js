// app/models/UserLogs.js
const mongoose = require('mongoose');

const UserLogsSchema = new mongoose.Schema({
  userId: { type: String, required: true },
  action: { type: String, required: true }, // 예: 'login', 'login_failed', 'password_reset'
  details: { type: String },
  ip: { type: String },
  timestamp: { type: Date, default: Date.now, index: true },
});

mongoose.model('UserLogs', UserLogsSchema);
