// app/middlewares/rateLimit.middleware.js
// 로그인·인증코드처럼 무차별 대입을 막아야 하는 API에 거는 간단한 횟수 제한 (메모리 기반)
module.exports = function rateLimit({ windowMs, max, keyFn, message }) {
  const hits = new Map();

  setInterval(() => {
    const now = Date.now();
    for (const [k, v] of hits) if (v.resetAt <= now) hits.delete(k);
  }, windowMs).unref();

  return (req, res, next) => {
    const key = (keyFn ? keyFn(req) : '') + '|' + req.ip;
    const now = Date.now();
    let entry = hits.get(key);
    if (!entry || entry.resetAt <= now) {
      entry = { count: 0, resetAt: now + windowMs };
      hits.set(key, entry);
    }
    entry.count += 1;
    if (entry.count > max) {
      const retrySec = Math.ceil((entry.resetAt - now) / 1000);
      res.set('Retry-After', String(retrySec));
      return res.status(429).json({ message: message || `요청이 너무 많습니다. ${retrySec}초 후 다시 시도하세요.` });
    }
    next();
  };
};
