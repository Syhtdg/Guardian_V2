// app/models/UserInfo.js
const mongoose = require('mongoose');
const { hashPassword, verifyPassword } = require('../utils/password');

const UserSchema = new mongoose.Schema({
  ID: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    match: /^[a-zA-Z0-9]{4,20}$/,
  },
  PASSWORD: { type: String, required: true }, // "scrypt$salt$hash" (예전 계정은 SHA-512 hex)
  EMAIL: { type: String, required: true, unique: true, trim: true, lowercase: true },
  NAME: { type: String, required: true, trim: true },
  salt: { type: String }, // 예전 SHA-512 방식 계정에만 남아 있음. 로그인하면 지워집니다.
  created: { type: Date, default: Date.now },
});

UserSchema.methods.setPassword = function (plain) {
  this.PASSWORD = hashPassword(plain);
  this.salt = undefined;
};

/** 비밀번호 확인. 예전 방식 계정이면 새 방식으로 바꿔 저장합니다. */
UserSchema.methods.checkPassword = async function (plain) {
  const { ok, legacy } = verifyPassword(plain, this.PASSWORD, this.salt);
  if (ok && legacy) {
    this.setPassword(plain);
    await this.save();
  }
  return ok;
};

mongoose.model('UserInfo', UserSchema);
