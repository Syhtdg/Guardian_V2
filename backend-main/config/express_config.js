// config/express_config.js
const path = require('path');
const http = require('http');
const express = require('express');
const cors = require('cors');
const { Server } = require('socket.io');
const config = require('./env');

module.exports = () => {
  const app = express();
  const server = http.createServer(app);

  const corsOptions = { origin: config.corsOrigins, credentials: true };
  const io = new Server(server, { cors: corsOptions, maxHttpBufferSize: 1e6 });
  app.set('io', io);

  app.disable('x-powered-by');
  app.use(cors(corsOptions));
  // 스냅샷 이미지(base64)가 들어오므로 기본 100kb 보다 크게 허용
  app.use(express.json({ limit: '5mb' }));
  app.use(express.urlencoded({ extended: false }));

  // 감지 스냅샷 이미지 (파일 이름이 무작위라 추측하기 어렵습니다)
  app.use('/snapshots', express.static(path.join(config.uploadDir, 'snapshots'), { maxAge: '7d' }));

  app.use('/', require('../app/routes/user.api.routes'));

  // 없는 경로
  app.use((req, res) => res.status(404).json({ message: '존재하지 않는 API입니다.' }));

  // JSON 형식 오류 등
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    if (err.type === 'entity.parse.failed') return res.status(400).json({ message: 'JSON 형식이 올바르지 않습니다.' });
    if (err.type === 'entity.too.large') return res.status(413).json({ message: '요청이 너무 큽니다.' });
    console.error(err);
    res.status(500).json({ message: '서버 오류' });
  });

  require('./socketio')(io);

  return { app, server, io };
};
