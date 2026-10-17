// server.js
const config = require('./config/env');
const connectDB = require('./config/mongoose_config');
const { server } = require('./config/express_config')();

connectDB().then(() => {
  server.listen(config.port, () => {
    console.log(`Guardian 백엔드 실행 중: http://localhost:${config.port}`);
    console.log(`허용된 프런트 주소: ${config.corsOrigins.join(', ')}`);
  });
});
