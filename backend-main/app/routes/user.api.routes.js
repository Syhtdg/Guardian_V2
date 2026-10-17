// app/routes/user.api.routes.js
const express = require('express');
const router = express.Router();

const user = require('../controllers/user.controller');
const ai = require('../controllers/ai.controller');
const cctv = require('../controllers/cctv.controller');
const requireLogin = require('../middlewares/jwt.middleware');
const requireApiKey = require('../middlewares/apiKey.middleware');
const rateLimit = require('../middlewares/rateLimit.middleware');

const MIN = 60 * 1000;
const byId = req => String((req.body && req.body.ID) || '');
const loginLimit = rateLimit({ windowMs: 10 * MIN, max: 10, keyFn: byId, message: '로그인 시도가 너무 많습니다. 10분 후 다시 시도하세요.' });
const mailLimit = rateLimit({ windowMs: 10 * MIN, max: 5, message: '메일 요청이 너무 많습니다. 10분 후 다시 시도하세요.' });
const resetLimit = rateLimit({ windowMs: 10 * MIN, max: 10, keyFn: byId });
const signupLimit = rateLimit({ windowMs: 60 * MIN, max: 20 });

// 상태 확인
router.get('/health', (req, res) => res.json({ ok: true }));

// 계정 (로그인 불필요)
router.post('/login', loginLimit, user.login);
router.post('/register', signupLimit, user.register);
router.post('/findID', mailLimit, user.findID);
router.post('/password/code', mailLimit, user.requestResetCode);
router.post('/password/reset', resetLimit, user.resetPassword);

// 로그인 필요
router.get('/me', requireLogin, user.me);
router.post('/log/save', requireLogin, user.saveLog);
router.get('/log/all', requireLogin, user.getAllLogs);
router.get('/ai/result/all', requireLogin, ai.getAllResults);
router.get('/ai/error/all', requireLogin, ai.getAiErrorLogs);
router.get('/cctv/public', requireLogin, cctv.getPublicCctv);

// YOLO 감지 프로그램 전용 (X-API-Key 필요)
router.post('/ai/result', requireApiKey, ai.receiveResult);
router.post('/ai/error', requireApiKey, ai.saveAiErrorLog);

module.exports = router;
