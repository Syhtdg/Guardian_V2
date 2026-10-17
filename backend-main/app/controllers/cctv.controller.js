// app/controllers/cctv.controller.js
// 국가교통정보센터(ITS) 공공 CCTV 목록을 대신 가져와 대시보드 지도에 넘겨 줍니다.
// API 키를 브라우저에 노출하지 않으려고 서버를 거칩니다. 영상(HLS)은 브라우저가 CCTV 서버에서 직접 받습니다.
const crypto = require('crypto');
const config = require('../../config/env');

const ITS_URL = 'https://openapi.its.go.kr:9443/cctvInfo';
const CACHE_MS = 60 * 1000;        // 같은 범위는 1분 동안 다시 묻지 않음 (영상 주소의 토큰은 시간이 지나면 만료됨)
const MAX_SPAN = 1.0;              // 한 번에 조회할 수 있는 범위 (위·경도 1도 ≈ 약 100km)
const cache = new Map();

const num = v => (v === undefined || v === '' ? NaN : Number(v));

/** ITS 응답(JSON 또는 XML)을 [{name, lat, lng, url, format}] 로 바꿉니다. */
function parseItems(text) {
  try {
    const data = JSON.parse(text);
    const rows = data?.response?.data || [];
    return (Array.isArray(rows) ? rows : [rows]).map(r => ({
      name: r.cctvname, lat: Number(r.coordy), lng: Number(r.coordx), url: r.cctvurl, format: r.cctvformat,
    }));
  } catch {
    // 시험 키 등은 JSON 을 요청해도 XML 로 답하는 경우가 있어 간단히 읽습니다
    const tag = (block, name) => {
      const m = block.match(new RegExp(`<${name}>([^<]*)</${name}>`));
      return m ? m[1].trim() : '';
    };
    return [...text.matchAll(/<data>([\s\S]*?)<\/data>/g)].map(([, b]) => ({
      name: tag(b, 'cctvname'), lat: Number(tag(b, 'coordy')), lng: Number(tag(b, 'coordx')),
      url: tag(b, 'cctvurl').replace(/&amp;/g, '&'), format: tag(b, 'cctvformat'),
    }));
  }
}

async function fetchIts(type, box) {
  const q = new URLSearchParams({
    apiKey: config.itsApiKey,
    type,               // its: 국도, ex: 고속도로
    cctvType: '1',      // 1: 실시간 스트리밍(HLS)
    minX: box.minX, maxX: box.maxX, minY: box.minY, maxY: box.maxY,
    getType: 'json',
  });
  const res = await fetch(`${ITS_URL}?${q}`, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`ITS 응답 오류 (${res.status})`);
  return parseItems(await res.text()).map(it => ({ ...it, road: type === 'ex' ? '고속도로' : '국도' }));
}

exports.getPublicCctv = async (req, res) => {
  if (!config.itsApiKey) {
    return res.status(503).json({ message: '공공 CCTV 기능을 쓰려면 backend-main/.env 에 ITS_API_KEY 를 설정하세요.', code: 'NO_KEY' });
  }
  const box = { minX: num(req.query.minX), maxX: num(req.query.maxX), minY: num(req.query.minY), maxY: num(req.query.maxY) };
  if (Object.values(box).some(v => !Number.isFinite(v)) || box.minX >= box.maxX || box.minY >= box.maxY) {
    return res.status(400).json({ message: 'minX, maxX, minY, maxY(경도·위도 범위)가 필요합니다.' });
  }
  if (box.maxX - box.minX > MAX_SPAN || box.maxY - box.minY > MAX_SPAN) {
    return res.status(400).json({ message: '조회 범위가 너무 넓습니다. 지도를 확대해 주세요.', code: 'TOO_WIDE' });
  }
  for (const k of Object.keys(box)) box[k] = box[k].toFixed(4);

  const key = Object.values(box).join(',');
  const hit = cache.get(key);
  if (hit && Date.now() - hit.at < CACHE_MS) return res.json(hit.body);

  try {
    const results = await Promise.allSettled([fetchIts('its', box), fetchIts('ex', box)]);
    const byId = new Map(); // 같은 CCTV(이름·좌표)가 국도·고속도로 양쪽에 오면 하나만
    for (const it of results.filter(r => r.status === 'fulfilled').flatMap(r => r.value)) {
      if (!it.name || !Number.isFinite(it.lat) || !Number.isFinite(it.lng) || !/^https?:\/\//.test(it.url)) continue;
      const id = crypto.createHash('sha1').update(`${it.name}|${it.lat}|${it.lng}`).digest('hex').slice(0, 12);
      if (!byId.has(id)) byId.set(id, { ...it, id });
    }
    const items = [...byId.values()];
    if (!items.length && results.every(r => r.status === 'rejected')) throw results[0].reason;

    const body = { source: '국가교통정보센터(ITS)', testKey: config.itsApiKey === 'test', items };
    cache.set(key, { at: Date.now(), body });
    if (cache.size > 200) cache.delete(cache.keys().next().value);
    res.json(body);
  } catch (err) {
    console.error('공공 CCTV 조회 실패:', err.message);
    res.status(502).json({ message: '공공 CCTV 정보를 가져오지 못했습니다. 잠시 후 다시 시도하세요.' });
  }
};
