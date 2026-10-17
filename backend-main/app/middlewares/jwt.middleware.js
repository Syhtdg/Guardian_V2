// app/middlewares/jwt.middleware.js
// 로그인한 사용자만 통과시킵니다. (Authorization: Bearer <토큰>)
const jwt = require('jsonwebtoken');
const config = require('../../config/env');

module.exports = (req, res, next) => {
  const authHeader = req.headers.authorization || '';
  if (!authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ message: '로그인이 필요합니다.' });
  }

  try {
    req.user = jwt.verify(authHeader.slice(7), config.jwtSecret);
    next();
  } catch (err) {
    return res.status(401).json({ message: '로그인이 만료되었습니다. 다시 로그인해 주세요.' });
  }
};
