// config/socketio.js
// 로그인 토큰이 있는 대시보드만 실시간 알림을 받을 수 있게 합니다.
const jwt = require('jsonwebtoken');
const config = require('./env');

module.exports = function (io) {
  io.use((socket, next) => {
    const token = (socket.handshake.auth && socket.handshake.auth.token) || '';
    try {
      socket.user = jwt.verify(token, config.jwtSecret);
      next();
    } catch (err) {
      next(new Error('unauthorized'));
    }
  });

  io.on('connection', socket => {
    console.log(`[socket] 접속: ${socket.user.ID} (${socket.handshake.address})`);
    socket.on('disconnect', () => console.log(`[socket] 종료: ${socket.user.ID}`));
  });
};
