// tools/add_user.js
// 관리자 계정을 직접 만드는 스크립트 (회원가입을 막아 둔 경우에 사용)
// 사용법: node tools/add_user.js <아이디> <비밀번호> <이메일> <이름>
const mongoose = require('mongoose');
const config = require('../config/env');
const { validatePasswordRule } = require('../app/utils/password');
require('../app/models/UserInfo');

const [ID, PASSWORD, EMAIL, NAME] = process.argv.slice(2);
if (!ID || !PASSWORD || !EMAIL || !NAME) {
  console.log('사용법: node tools/add_user.js <아이디> <비밀번호> <이메일> <이름>');
  process.exit(1);
}
const pwError = validatePasswordRule(PASSWORD);
if (pwError) {
  console.error(pwError);
  process.exit(1);
}

(async () => {
  const major = Number(mongoose.version.split('.')[0]);
  await mongoose.connect(config.mongoUri, major < 6 ? { useNewUrlParser: true, useUnifiedTopology: true, useCreateIndex: true } : {});
  const UserInfo = mongoose.model('UserInfo');
  try {
    const user = new UserInfo({ ID, EMAIL, NAME });
    user.setPassword(PASSWORD);
    await user.save();
    console.log(`사용자 등록 완료: ${ID}`);
  } catch (err) {
    console.error('사용자 등록 실패:', err.code === 11000 ? '이미 있는 아이디 또는 이메일' : err.message);
  } finally {
    await mongoose.disconnect();
  }
})();
