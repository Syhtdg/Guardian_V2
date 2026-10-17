// app/controllers/ai.controller.js
// YOLO 감지 프로그램(ai/detect.py)이 보내는 감지 결과와 오류를 저장하고 대시보드로 실시간 전송합니다.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const mongoose = require('mongoose');
const config = require('../../config/env');

require('../models/AiResult');
require('../models/AIErrorLog');
const AiResult = mongoose.model('AiResult');
const AiErrorLog = mongoose.model('AiErrorLog');

const SNAPSHOT_DIR = path.join(config.uploadDir, 'snapshots');
const MAX_IMAGE_BYTES = 3 * 1024 * 1024;

// 모델 클래스 이름이 영어여도 받아 줍니다.
const TYPE_ALIASES = { 불: '불', fire: '불', flame: '불', 화염: '불', 연기: '연기', smoke: '연기' };

const isNum = v => typeof v === 'number' && Number.isFinite(v);
const optStr = (v, max = 200) => (typeof v === 'string' && v.trim() ? v.trim().slice(0, max) : undefined);

function saveSnapshot(base64) {
  const data = base64.replace(/^data:image\/\w+;base64,/, '');
  const buf = Buffer.from(data, 'base64');
  if (buf.length === 0 || buf.length > MAX_IMAGE_BYTES) throw new Error('이미지 크기가 올바르지 않습니다 (최대 3MB).');
  // JPEG(FF D8) 또는 PNG(89 50) 만 허용
  const isJpeg = buf[0] === 0xff && buf[1] === 0xd8;
  const isPng = buf[0] === 0x89 && buf[1] === 0x50;
  if (!isJpeg && !isPng) throw new Error('JPEG 또는 PNG 이미지만 받을 수 있습니다.');

  fs.mkdirSync(SNAPSHOT_DIR, { recursive: true });
  const name = `${Date.now()}-${crypto.randomBytes(8).toString('hex')}.${isJpeg ? 'jpg' : 'png'}`;
  fs.writeFileSync(path.join(SNAPSHOT_DIR, name), buf);
  return `/snapshots/${name}`;
}

exports.receiveResult = async (req, res) => {
  const body = req.body || {};
  const type = TYPE_ALIASES[String(body.type || '').trim().toLowerCase()] || TYPE_ALIASES[String(body.type || '').trim()];
  const confidence = Number(body.confidence);
  const location = optStr(body.location);

  if (!type) return res.status(400).json({ message: 'type 은 "불" 또는 "연기" 여야 합니다.' });
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 100) {
    return res.status(400).json({ message: 'confidence 는 0~100 사이 퍼센트 값이어야 합니다.' });
  }
  if (!location) return res.status(400).json({ message: 'location 이 필요합니다.' });

  const doc = {
    type,
    confidence: Math.round(confidence * 10) / 10,
    location,
    cameraId: optStr(body.cameraId, 50),
    timestamp: new Date(),
  };
  if (isNum(body.latitude) && isNum(body.longitude)) {
    doc.latitude = body.latitude;
    doc.longitude = body.longitude;
  }
  if (Array.isArray(body.bbox) && body.bbox.length === 4 && body.bbox.every(isNum)) doc.bbox = body.bbox;
  // 실시간 영상 주소는 http(s) 만 받습니다 (rtsp 주소에는 계정 정보가 들어 있을 수 있음)
  if (typeof body.streamUrl === 'string' && /^https?:\/\//.test(body.streamUrl) && body.streamUrl.length <= 1000) {
    doc.streamUrl = body.streamUrl;
  }

  try {
    if (typeof body.image === 'string' && body.image) doc.imageUrl = saveSnapshot(body.image);
  } catch (err) {
    return res.status(400).json({ message: err.message });
  }

  try {
    const saved = await new AiResult(doc).save();
    req.app.get('io').emit('aiResult', saved);
    res.status(201).json({ message: 'AI 결과 저장 완료', id: saved._id });
  } catch (err) {
    console.error('AI 결과 저장 실패:', err);
    res.status(500).json({ message: '서버 오류' });
  }
};

exports.getAllResults = async (req, res) => {
  try {
    const filter = {};
    if (req.query.type === '불' || req.query.type === '연기') filter.type = req.query.type;
    if (req.query.from || req.query.to) {
      const from = req.query.from ? new Date(req.query.from) : null;
      const to = req.query.to ? new Date(req.query.to) : null;
      if ((from && isNaN(from)) || (to && isNaN(to))) {
        return res.status(400).json({ message: 'from/to 는 올바른 날짜여야 합니다 (예: 2026-10-15).' });
      }
      filter.timestamp = {};
      if (from) filter.timestamp.$gte = from;
      if (to) filter.timestamp.$lte = to;
    }
    const limit = Math.min(Number(req.query.limit) || 500, 2000);
    const results = await AiResult.find(filter).sort({ timestamp: -1 }).limit(limit);
    res.status(200).json(results);
  } catch (err) {
    console.error('AI 결과 조회 실패:', err);
    res.status(500).json({ message: '서버 오류' });
  }
};

exports.saveAiErrorLog = async (req, res) => {
  const body = req.body || {};
  const errorType = optStr(body.errorType, 100);
  if (!errorType) return res.status(400).json({ message: 'errorType 이 필요합니다.' });

  try {
    const log = await new AiErrorLog({
      errorType,
      message: optStr(body.message, 2000),
      location: optStr(body.location),
      cameraId: optStr(body.cameraId, 50),
      rawData: body.rawData && typeof body.rawData === 'object' ? body.rawData : undefined,
    }).save();
    req.app.get('io').emit('aiError', log);
    res.status(201).json({ message: 'AI 에러 로그 저장 성공' });
  } catch (err) {
    console.error('AI 에러 로그 저장 실패:', err);
    res.status(500).json({ message: '로그 저장 실패' });
  }
};

exports.getAiErrorLogs = async (req, res) => {
  try {
    const limit = Math.min(Number(req.query.limit) || 500, 2000);
    const logs = await AiErrorLog.find().sort({ timestamp: -1 }).limit(limit);
    res.status(200).json(logs);
  } catch (err) {
    console.error('에러 로그 조회 실패:', err);
    res.status(500).json({ message: '에러 로그 조회 실패' });
  }
};
