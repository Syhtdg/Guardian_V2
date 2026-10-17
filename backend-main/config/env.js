// config/env.js
// .env 파일을 읽어 설정값을 한곳에 모읍니다. (dotenv 없이 동작하는 간단한 파서)
const fs = require('fs');
const path = require('path');

function loadDotEnv(file) {
  if (!fs.existsSync(file)) return;
  const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    // 이미 셸에서 지정한 환경변수가 있으면 그쪽을 우선합니다.
    if (process.env[key] === undefined) process.env[key] = value;
  }
}

loadDotEnv(path.join(__dirname, '..', '.env'));

function required(name) {
  const v = process.env[name];
  if (!v) {
    console.error(`\n[설정 오류] 환경변수 ${name} 가 비어 있습니다.`);
    console.error('backend-main/.env.example 을 .env 로 복사한 뒤 값을 채워 주세요.\n');
    process.exit(1);
  }
  return v;
}

const config = {
  nodeEnv: process.env.NODE_ENV || 'development',
  port: Number(process.env.PORT || 10111),
  mongoUri: process.env.MONGO_URI || 'mongodb://localhost:27017/fire-detection-dev',
  jwtSecret: required('JWT_SECRET'),
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '2h',
  aiApiKey: required('AI_API_KEY'),
  corsOrigins: (process.env.CORS_ORIGIN || 'http://localhost:3000')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean),
  allowSignup: (process.env.ALLOW_SIGNUP || 'true') === 'true',
  uploadDir: path.resolve(__dirname, '..', process.env.UPLOAD_DIR || 'uploads'),
  // 국가교통정보센터(ITS) 공공 CCTV 오픈API 키 (비워 두면 공공 CCTV 지도 기능이 꺼집니다)
  itsApiKey: process.env.ITS_API_KEY || '',
  smtp: {
    host: process.env.SMTP_HOST || '',
    port: Number(process.env.SMTP_PORT || 465),
    user: process.env.SMTP_USER || '',
    pass: process.env.SMTP_PASS || '',
    from: process.env.MAIL_FROM || process.env.SMTP_USER || '',
  },
};

if (config.jwtSecret.length < 32) {
  console.warn('[경고] JWT_SECRET 이 너무 짧습니다. 32자 이상 무작위 문자열을 쓰세요.');
}

module.exports = config;
