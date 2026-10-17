// app/utils/mailer.js
// SMTP 설정이 있으면 nodemailer로 메일을 보내고, 없으면 서버 콘솔에 내용을 출력합니다(개발용).
const config = require('../../config/env');

let transporter = null;

function getTransporter() {
  if (transporter) return transporter;
  const nodemailer = require('nodemailer');
  transporter = nodemailer.createTransport({
    host: config.smtp.host,
    port: config.smtp.port,
    secure: config.smtp.port === 465,
    auth: { user: config.smtp.user, pass: config.smtp.pass },
  });
  return transporter;
}

function smtpConfigured() {
  return Boolean(config.smtp.host && config.smtp.user && config.smtp.pass);
}

async function sendMail({ to, subject, text }) {
  if (!smtpConfigured()) {
    console.log('\n========== [메일 미설정: 콘솔 출력] ==========');
    console.log(`받는 사람: ${to}\n제목: ${subject}\n\n${text}`);
    console.log('==============================================\n');
    return;
  }
  await getTransporter().sendMail({ from: config.smtp.from, to, subject, text });
}

module.exports = { sendMail, smtpConfigured };
