// app/middlewares/apiKey.middleware.js
// YOLO 감지 프로그램만 감지 결과를 올릴 수 있게 합니다. (X-API-Key 헤더)
const crypto = require('crypto');
const config = require('../../config/env');

const expected = Buffer.from(config.aiApiKey);

module.exports = (req, res, next) => {
  const given = Buffer.from(String(req.headers['x-api-key'] || ''));
  const ok = given.length === expected.length && crypto.timingSafeEqual(given, expected);
  if (!ok) return res.status(401).json({ message: '유효하지 않은 API 키입니다.' });
  next();
};
