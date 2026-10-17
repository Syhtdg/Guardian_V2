// app/utils/password.js
// 비밀번호 해시: Node 내장 scrypt 사용 (추가 패키지 불필요)
// 저장 형식: "scrypt$<salt hex>$<hash hex>"
// 예전 방식(SHA-512 + salt 필드)으로 저장된 계정도 로그인되며, 로그인 시 새 방식으로 자동 변환됩니다.
const crypto = require('crypto');

const KEYLEN = 64;

function hashPassword(plain) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(plain, salt, KEYLEN).toString('hex');
  return `scrypt$${salt}$${hash}`;
}

function safeEqualHex(a, b) {
  const ba = Buffer.from(a, 'hex');
  const bb = Buffer.from(b, 'hex');
  return ba.length === bb.length && ba.length > 0 && crypto.timingSafeEqual(ba, bb);
}

/**
 * @returns {{ ok: boolean, legacy: boolean }}
 */
function verifyPassword(plain, stored, legacySalt) {
  if (typeof plain !== 'string' || typeof stored !== 'string') return { ok: false, legacy: false };

  if (stored.startsWith('scrypt$')) {
    const [, salt, hash] = stored.split('$');
    const test = crypto.scryptSync(plain, salt, KEYLEN).toString('hex');
    return { ok: safeEqualHex(test, hash), legacy: false };
  }

  // 예전 방식: sha512(PASSWORD + salt)
  if (legacySalt) {
    const test = crypto.createHash('sha512').update(plain + legacySalt).digest('hex');
    return { ok: safeEqualHex(test, stored), legacy: true };
  }
  return { ok: false, legacy: false };
}

function validatePasswordRule(pw) {
  if (typeof pw !== 'string' || pw.length < 8) return '비밀번호는 8자 이상이어야 합니다.';
  if (pw.length > 72) return '비밀번호는 72자 이하로 입력해 주세요.';
  if (!/[A-Za-z]/.test(pw) || !/[0-9]/.test(pw)) return '비밀번호에 영문과 숫자를 모두 포함해 주세요.';
  return null;
}

module.exports = { hashPassword, verifyPassword, validatePasswordRule };
