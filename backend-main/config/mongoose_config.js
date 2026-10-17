// config/mongoose_config.js
const mongoose = require('mongoose');
const config = require('./env');

module.exports = function () {
  // 모델 등록
  require('../app/models/UserInfo');
  require('../app/models/UserLogs');
  require('../app/models/AiResult');
  require('../app/models/AIErrorLog');
  require('../app/models/VerificationCode');

  const major = Number(mongoose.version.split('.')[0]);
  const options = major < 6 ? { useNewUrlParser: true, useUnifiedTopology: true, useCreateIndex: true } : {};

  return mongoose
    .connect(config.mongoUri, options)
    .then(() => console.log(`MongoDB 연결 완료 (mongoose ${mongoose.version})`))
    .catch(err => {
      console.error('MongoDB 연결 실패:', err.message);
      console.error('MongoDB가 실행 중인지, .env 의 MONGO_URI 가 맞는지 확인하세요.');
      process.exit(1);
    });
};
