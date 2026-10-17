// app/models/VerificationCode.js
// 비밀번호 재설정용 6자리 인증코드. 코드 자체가 아니라 해시만 저장합니다.
const mongoose = require('mongoose');

const VerificationCodeSchema = new mongoose.Schema({
  userId: { type: String, required: true, index: true },
  purpose: { type: String, required: true, default: 'password_reset' },
  codeHash: { type: String, required: true },
  attempts: { type: Number, default: 0 },
  // expiresAt 이 지나면 MongoDB가 자동으로 문서를 지웁니다 (TTL 인덱스)
  expiresAt: { type: Date, required: true, index: { expires: 0 } },
});

mongoose.model('VerificationCode', VerificationCodeSchema);
