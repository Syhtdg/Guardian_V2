// app/controllers/user.controller.js
const crypto = require('crypto');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const config = require('../../config/env');
const { validatePasswordRule } = require('../utils/password');
const { sendMail } = require('../utils/mailer');

require('../models/UserInfo');
require('../models/UserLogs');
require('../models/VerificationCode');
const UserInfo = mongoose.model('UserInfo');
const UserLogs = mongoose.model('UserLogs');
const VerificationCode = mongoose.model('VerificationCode');

const CODE_TTL_MIN = 10;
const CODE_MAX_ATTEMPTS = 5;

const str = v => (typeof v === 'string' ? v.trim() : '');
const escapeRegex = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const emailQuery = email => new RegExp(`^${escapeRegex(email)}$`, 'i');
const isEmail = s => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
const hashCode = code => crypto.createHash('sha256').update(code).digest('hex');

async function writeLog(userId, action, details, ip) {
  try {
    await new UserLogs({ userId, action, details, ip }).save();
  } catch (err) {
    console.error('사용자 로그 저장 실패:', err.message);
  }
}
exports.writeLog = writeLog;

// ───────────────────────── 로그인 / 회원가입 ─────────────────────────

exports.login = async (req, res) => {
  const ID = str(req.body.ID);
  const PASSWORD = typeof req.body.PASSWORD === 'string' ? req.body.PASSWORD : '';
  if (!ID || !PASSWORD) return res.status(400).json({ message: '아이디와 비밀번호를 입력해 주세요.' });

  try {
    const user = await UserInfo.findOne({ ID });
    // 아이디가 없는지 비밀번호가 틀렸는지 구분하지 않습니다 (계정 존재 여부 노출 방지)
    if (!user || !(await user.checkPassword(PASSWORD))) {
      await writeLog(ID, 'login_failed', '아이디 또는 비밀번호 불일치', req.ip);
      return res.status(401).json({ message: '아이디 또는 비밀번호가 올바르지 않습니다.' });
    }

    const token = jwt.sign({ ID: user.ID, NAME: user.NAME }, config.jwtSecret, { expiresIn: config.jwtExpiresIn });
    await writeLog(user.ID, 'login', '로그인 성공', req.ip);
    return res.status(200).json({ message: '로그인 성공', token, user: { ID: user.ID, NAME: user.NAME } });
  } catch (error) {
    console.error('로그인 오류:', error);
    return res.status(500).json({ message: '서버 오류' });
  }
};

exports.register = async (req, res) => {
  if (!config.allowSignup) return res.status(403).json({ message: '현재 회원가입이 막혀 있습니다. 관리자에게 문의하세요.' });

  const ID = str(req.body.ID);
  const EMAIL = str(req.body.EMAIL).toLowerCase();
  const NAME = str(req.body.NAME);
  const PASSWORD = req.body.PASSWORD;

  if (!/^[a-zA-Z0-9]{4,20}$/.test(ID)) return res.status(400).json({ message: '아이디는 영문·숫자 4~20자로 입력해 주세요.' });
  const pwError = validatePasswordRule(PASSWORD);
  if (pwError) return res.status(400).json({ message: pwError });
  if (!isEmail(EMAIL)) return res.status(400).json({ message: '이메일 형식이 올바르지 않습니다.' });
  if (!NAME || NAME.length > 30) return res.status(400).json({ message: '이름을 입력해 주세요.' });

  try {
    if (await UserInfo.findOne({ ID })) return res.status(400).json({ message: '이미 존재하는 ID입니다.' });
    if (await UserInfo.findOne({ EMAIL: emailQuery(EMAIL) })) return res.status(400).json({ message: '이미 등록된 이메일입니다.' });

    const user = new UserInfo({ ID, EMAIL, NAME });
    user.setPassword(PASSWORD);
    await user.save();
    await writeLog(ID, 'register', '회원가입', req.ip);
    return res.status(201).json({ message: '회원가입 성공!' });
  } catch (error) {
    if (error && error.code === 11000) return res.status(400).json({ message: '이미 사용 중인 아이디 또는 이메일입니다.' });
    console.error('회원가입 오류:', error);
    return res.status(500).json({ message: '서버 오류' });
  }
};

// ───────────────────────── 아이디 찾기 ─────────────────────────
// 화면에 아이디를 바로 보여 주지 않고, 등록된 이메일로 보냅니다.

exports.findID = async (req, res) => {
  const NAME = str(req.body.NAME);
  const EMAIL = str(req.body.EMAIL);
  if (!NAME || !isEmail(EMAIL)) return res.status(400).json({ message: '이름과 이메일을 정확히 입력해 주세요.' });

  const reply = { message: '입력한 정보와 일치하는 계정이 있으면 이메일로 아이디를 보냈습니다.' };
  try {
    const user = await UserInfo.findOne({ NAME, EMAIL: emailQuery(EMAIL) });
    if (user) {
      await sendMail({
        to: user.EMAIL,
        subject: '[Guardian] 아이디 안내',
        text: `${user.NAME}님의 Guardian 아이디는 "${user.ID}" 입니다.\n\n본인이 요청하지 않았다면 이 메일을 무시하세요.`,
      });
      await writeLog(user.ID, 'find_id', '아이디 찾기 메일 발송', req.ip);
    }
    return res.status(200).json(reply);
  } catch (err) {
    console.error('아이디 찾기 오류:', err);
    return res.status(500).json({ message: '메일 발송 중 오류가 발생했습니다.' });
  }
};

// ───────────────────────── 비밀번호 재설정 (이메일 인증코드) ─────────────────────────

// 1단계: 아이디 + 이메일 → 인증코드 메일 발송
exports.requestResetCode = async (req, res) => {
  const ID = str(req.body.ID);
  const EMAIL = str(req.body.EMAIL);
  if (!ID || !isEmail(EMAIL)) return res.status(400).json({ message: '아이디와 이메일을 정확히 입력해 주세요.' });

  const reply = { message: `입력한 정보가 맞으면 이메일로 인증코드를 보냈습니다. (${CODE_TTL_MIN}분 동안 유효)` };
  try {
    const user = await UserInfo.findOne({ ID, EMAIL: emailQuery(EMAIL) });
    if (!user) return res.status(200).json(reply); // 계정 존재 여부를 알려 주지 않음

    const code = String(crypto.randomInt(0, 1000000)).padStart(6, '0');
    await VerificationCode.deleteMany({ userId: user.ID, purpose: 'password_reset' });
    await new VerificationCode({
      userId: user.ID,
      purpose: 'password_reset',
      codeHash: hashCode(code),
      expiresAt: new Date(Date.now() + CODE_TTL_MIN * 60 * 1000),
    }).save();

    await sendMail({
      to: user.EMAIL,
      subject: '[Guardian] 비밀번호 재설정 인증코드',
      text: `인증코드: ${code}\n\n${CODE_TTL_MIN}분 안에 입력해 주세요.\n본인이 요청하지 않았다면 이 메일을 무시하세요.`,
    });
    await writeLog(user.ID, 'reset_code_sent', '비밀번호 재설정 인증코드 발송', req.ip);
    return res.status(200).json(reply);
  } catch (err) {
    console.error('인증코드 발송 오류:', err);
    return res.status(500).json({ message: '메일 발송 중 오류가 발생했습니다.' });
  }
};

// 2단계: 아이디 + 이메일 + 인증코드 + 새 비밀번호 → 변경
exports.resetPassword = async (req, res) => {
  const ID = str(req.body.ID);
  const EMAIL = str(req.body.EMAIL);
  const code = str(req.body.code);
  const { newPassword } = req.body;

  if (!ID || !isEmail(EMAIL) || !/^\d{6}$/.test(code)) {
    return res.status(400).json({ message: '아이디, 이메일, 6자리 인증코드를 입력해 주세요.' });
  }
  const pwError = validatePasswordRule(newPassword);
  if (pwError) return res.status(400).json({ message: pwError });

  const invalid = () => res.status(400).json({ message: '인증코드가 올바르지 않거나 만료되었습니다.' });
  try {
    const user = await UserInfo.findOne({ ID, EMAIL: emailQuery(EMAIL) });
    if (!user) return invalid();

    const record = await VerificationCode.findOne({ userId: user.ID, purpose: 'password_reset' });
    if (!record || record.expiresAt.getTime() < Date.now()) return invalid();

    if (record.attempts >= CODE_MAX_ATTEMPTS) {
      await VerificationCode.deleteMany({ userId: user.ID, purpose: 'password_reset' });
      return res.status(429).json({ message: '인증코드 입력 횟수를 초과했습니다. 코드를 다시 받아 주세요.' });
    }

    const given = Buffer.from(hashCode(code), 'hex');
    const stored = Buffer.from(record.codeHash, 'hex');
    if (given.length !== stored.length || !crypto.timingSafeEqual(given, stored)) {
      record.attempts += 1;
      await record.save();
      return invalid();
    }

    user.setPassword(newPassword);
    await user.save();
    await VerificationCode.deleteMany({ userId: user.ID, purpose: 'password_reset' });
    await writeLog(user.ID, 'password_reset', '이메일 인증 후 비밀번호 변경', req.ip);
    return res.status(200).json({ message: '비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요.' });
  } catch (err) {
    console.error('비밀번호 재설정 오류:', err);
    return res.status(500).json({ message: '서버 오류' });
  }
};

// ───────────────────────── 사용자 로그 ─────────────────────────

exports.saveLog = async (req, res) => {
  const action = str(req.body.action);
  if (!action) return res.status(400).json({ message: 'action 값이 필요합니다.' });
  try {
    // userId 는 요청 본문이 아니라 로그인 토큰에서 가져옵니다 (남의 이름으로 기록 방지)
    const log = await new UserLogs({ userId: req.user.ID, action, details: str(req.body.details), ip: req.ip }).save();
    req.app.get('io').emit('newLog', log);
    res.status(201).json({ message: '로그 저장 성공' });
  } catch (err) {
    console.error('로그 저장 실패:', err);
    res.status(500).json({ message: '로그 저장 실패' });
  }
};

exports.getAllLogs = async (req, res) => {
  try {
    const limit = Math.min(Number(req.query.limit) || 500, 2000);
    const logs = await UserLogs.find().sort({ timestamp: -1 }).limit(limit);
    res.status(200).json(logs);
  } catch (err) {
    console.error('로그 조회 실패:', err);
    res.status(500).json({ message: '로그 조회 실패' });
  }
};

exports.me = (req, res) => res.json({ ID: req.user.ID, NAME: req.user.NAME });
