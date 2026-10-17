<template>
  <div class="landing">
    <!-- 상단 -->
    <header class="top">
      <img src="@/assets/logo_3d.png" alt="Guardian" class="brand" />
      <nav class="top-nav d-none d-md-flex">
        <a href="#features">기능</a>
        <a href="#how">구성</a>
        <a href="#model">AI 성능</a>
      </nav>
      <v-btn v-if="loggedIn" to="/dashboard" color="primary" variant="flat" append-icon="mdi-arrow-right">대시보드</v-btn>
      <v-btn v-else to="/login" color="primary" variant="flat">로그인</v-btn>
    </header>

    <!-- 히어로 -->
    <section class="hero">
      <div class="hero-text">
        <v-chip color="primary" variant="tonal" size="small" prepend-icon="mdi-fire-alert" class="mb-4">AI 화재·연기 감지 관제 시스템</v-chip>
        <h1>카메라가 먼저 보고,<br /><span class="accent">먼저 알립니다.</span></h1>
        <p class="lead">
          CCTV·웹캠 영상에서 YOLO 모델이 불과 연기를 찾아내면,
          관제 화면에 경보음·스냅샷·지도 위치와 함께 즉시 알려 줍니다.
        </p>
        <div class="cta">
          <v-btn :to="loggedIn ? '/dashboard' : '/login'" color="primary" size="large" variant="flat" prepend-icon="mdi-monitor-dashboard">
            {{ loggedIn ? '대시보드 열기' : '관제 화면 들어가기' }}
          </v-btn>
          <v-btn href="https://github.com/Syhtdg/Guardian" target="_blank" rel="noopener" size="large" variant="outlined" prepend-icon="mdi-github">
            소스 코드
          </v-btn>
        </div>
      </div>
      <div class="hero-art">
        <img :src="heroImg" alt="카메라 화면에서 불과 연기를 감지해 경보를 띄우는 모습" />
      </div>
    </section>

    <!-- 수치 -->
    <section class="stats">
      <div v-for="s in stats" :key="s.label" class="stat">
        <div class="stat-value">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </section>

    <!-- 기능 -->
    <section id="features" class="section">
      <h2>주요 기능</h2>
      <p class="section-sub">감지부터 기록까지, 관제 요원이 바로 판단할 수 있게.</p>
      <div class="features">
        <v-card v-for="f in features" :key="f.title" class="feature">
          <div class="feature-icon" :style="{ background: f.bg, color: f.fg }"><v-icon :icon="f.icon" size="26" /></div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </v-card>
      </div>
    </section>

    <!-- 구성 -->
    <section id="how" class="section">
      <h2>어떻게 동작하나요</h2>
      <p class="section-sub">감지기 → 서버 → 대시보드. 각 구간은 API 키와 로그인 토큰으로 보호됩니다.</p>
      <div class="arch"><img :src="archImg" alt="카메라, AI 감지기, API 서버, 관제 대시보드로 이어지는 시스템 구성도" /></div>
      <div class="stack">
        <v-chip v-for="t in stack" :key="t" variant="outlined" size="small">{{ t }}</v-chip>
      </div>
    </section>

    <!-- 모델 -->
    <section id="model" class="section">
      <h2>AI 모델</h2>
      <p class="section-sub">AI Hub 「화재 발생 예측 영상」으로 YOLO11s 를 학습했습니다. 같은 영상의 프레임이 학습·검증에 섞이지 않게 영상 단위로 나눴습니다.</p>
      <div class="model">
        <v-card class="model-card">
          <div v-for="m in metrics" :key="m.label" class="metric">
            <div class="metric-head">
              <span><v-icon :icon="m.icon" size="18" class="mr-1" :color="m.color" />{{ m.label }}</span>
              <span class="metric-num">{{ m.value.toFixed(3) }}</span>
            </div>
            <v-progress-linear :model-value="m.value * 100" :color="m.color" height="8" rounded />
          </div>
          <p class="metric-note">검증 1.6만 장 기준 mAP50. 실제 카메라 환경에서는 더 낮을 수 있습니다.</p>
        </v-card>
        <div class="model-points">
          <div v-for="p in modelPoints" :key="p.title" class="point">
            <v-icon :icon="p.icon" color="primary" class="mr-3" />
            <div>
              <div class="point-title">{{ p.title }}</div>
              <div class="point-desc">{{ p.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <footer class="foot">
      <div>Guardian · 2025 캡스톤 프로젝트 → 2026 v2</div>
      <div class="foot-sub">학습 데이터: AI Hub 「화재 발생 예측 영상」 · 배경 사진: Unsplash(matt-c) · 지도: 카카오맵 · 날씨: Open-Meteo</div>
    </footer>
  </div>
</template>

<script setup>
import { isLoggedIn } from '@/utils/auth'
import heroImg from '@/assets/illust/hero.svg'
import archImg from '@/assets/illust/architecture.svg'

const loggedIn = isLoggedIn()

const stats = [
  { value: '0.803', label: 'mAP50 (불·연기)' },
  { value: '9.6만 장', label: '학습 이미지' },
  { value: '10프레임 중 4회', label: '감지 확정 기준' },
  { value: '실시간', label: 'socket.io 경보' }
]

const features = [
  { icon: 'mdi-fire-alert', title: '실시간 불·연기 감지', desc: '웹캠·RTSP·영상 파일을 YOLO 로 분석하고, 깜빡이는 오탐은 여러 프레임 확인으로 거릅니다.', bg: 'rgba(255,90,54,.15)', fg: '#ff8a65' },
  { icon: 'mdi-bell-ring-outline', title: '즉시 경보', desc: '감지 순간 팝업·경보음·스냅샷을 띄우고, 같은 종류는 쿨다운으로 반복 알림을 막습니다.', bg: 'rgba(229,57,53,.15)', fg: '#ff6b66' },
  { icon: 'mdi-map-marker-radius-outline', title: '위치 확인', desc: '카메라 좌표를 지도에 불·연기 아이콘으로 표시하고, 기록을 누르면 해당 위치로 이동합니다.', bg: 'rgba(78,168,255,.15)', fg: '#7cc0ff' },
  { icon: 'mdi-shield-lock-outline', title: '안전한 운영', desc: '감지기 전용 API 키, JWT 로그인, 인증코드 비밀번호 재설정, 요청 횟수 제한을 갖췄습니다.', bg: 'rgba(46,204,113,.15)', fg: '#6fdc9c' }
]

const stack = ['Python', 'YOLO11s', 'PyTorch', 'OpenCV', 'Node.js', 'Express', 'MongoDB', 'socket.io', 'JWT', 'Vue 3', 'Vuetify', 'Vite', '카카오맵']

const metrics = [
  { label: '불', value: 0.872, icon: 'mdi-fire', color: 'fire' },
  { label: '연기', value: 0.733, icon: 'mdi-weather-fog', color: 'smoke' },
  { label: '전체', value: 0.803, icon: 'mdi-chart-line', color: 'primary' }
]

const modelPoints = [
  { icon: 'mdi-filter-check-outline', title: '확정 로직으로 오탐 감소', desc: '한 프레임이 아니라 최근 10프레임 중 4번 이상 잡혀야 알림. 학습에 안 쓴 평범한 사진의 오탐률은 1.9%.' },
  { icon: 'mdi-chart-timeline-variant', title: '알림 기준으로 평가', desc: 'mAP 외에 실제 알림 로직을 영상 단위로 재현해 감지 지연과 오경보를 비교하고 설정값을 정했습니다.' },
  { icon: 'mdi-alert-circle-outline', title: '한계도 투명하게', desc: '연기는 불보다 놓치기 쉽고, 학습 데이터는 야외 영상뿐입니다. 실내·야간은 추가 검증이 필요합니다.' }
]
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background:
    radial-gradient(1200px 600px at 85% -10%, rgba(229, 57, 53, 0.18), transparent 60%),
    radial-gradient(900px 500px at -10% 30%, rgba(78, 168, 255, 0.07), transparent 60%),
    #0f1115;
  color: #e8ebef;
}
.top {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 14px clamp(16px, 5vw, 64px);
  background: rgba(15, 17, 21, 0.75);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand { height: 32px; width: auto; }
.top-nav { gap: 22px; margin-left: auto; margin-right: 8px; }
.top > .v-btn { margin-left: auto; }
.top-nav.d-md-flex ~ .v-btn { margin-left: 0; }
.top-nav a { color: rgba(255, 255, 255, 0.7); text-decoration: none; font-size: 14px; }
.top-nav a:hover { color: #fff; }

.hero {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 40px;
  align-items: center;
  max-width: 1240px;
  margin: 0 auto;
  padding: 72px clamp(16px, 5vw, 64px) 40px;
}
.hero h1 { font-size: clamp(34px, 4.6vw, 54px); line-height: 1.2; font-weight: 800; letter-spacing: -0.5px; }
.accent { background: linear-gradient(90deg, #ff6a3d, #ff3b30); -webkit-background-clip: text; background-clip: text; color: transparent; }
.lead { margin: 20px 0 30px; font-size: 17px; line-height: 1.75; color: rgba(255, 255, 255, 0.7); max-width: 520px; }
.cta { display: flex; flex-wrap: wrap; gap: 12px; }
.hero-art img { width: 100%; height: auto; display: block; }

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 clamp(16px, 5vw, 64px);
}
.stat {
  padding: 22px 12px;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}
.stat + .stat { border-left: 1px solid rgba(255, 255, 255, 0.07); }
.stat-value { font-size: 24px; font-weight: 800; }
.stat-label { font-size: 13px; color: rgba(255, 255, 255, 0.55); margin-top: 4px; }

.section { max-width: 1240px; margin: 0 auto; padding: 72px clamp(16px, 5vw, 64px) 0; }
.section h2 { font-size: 28px; font-weight: 800; }
.section-sub { color: rgba(255, 255, 255, 0.6); margin: 8px 0 28px; line-height: 1.6; }
.features { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.feature { padding: 22px; border: 1px solid rgba(255, 255, 255, 0.06); }
.feature-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
.feature h3 { font-size: 17px; font-weight: 700; margin-bottom: 8px; }
.feature p { font-size: 14px; line-height: 1.65; color: rgba(255, 255, 255, 0.65); }
.arch { overflow-x: auto; border-radius: 20px; }
.arch img { width: 100%; min-width: 760px; height: auto; display: block; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.06); }
.stack { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }

.model { display: grid; grid-template-columns: 1fr 1.1fr; gap: 24px; align-items: start; }
.model-card { padding: 24px; border: 1px solid rgba(255, 255, 255, 0.06); }
.metric + .metric { margin-top: 18px; }
.metric-head { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 15px; }
.metric-num { font-weight: 700; font-variant-numeric: tabular-nums; }
.metric-note { margin-top: 18px; font-size: 12px; color: rgba(255, 255, 255, 0.45); }
.point { display: flex; align-items: flex-start; padding: 16px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
.point:first-child { padding-top: 4px; }
.point-title { font-weight: 700; margin-bottom: 4px; }
.point-desc { font-size: 14px; line-height: 1.65; color: rgba(255, 255, 255, 0.65); }

.foot { max-width: 1240px; margin: 80px auto 0; padding: 28px clamp(16px, 5vw, 64px) 40px; border-top: 1px solid rgba(255, 255, 255, 0.07); font-size: 14px; color: rgba(255, 255, 255, 0.7); }
.foot-sub { margin-top: 6px; font-size: 12px; color: rgba(255, 255, 255, 0.4); }

@media (max-width: 959px) {
  .top-nav.d-md-flex ~ .v-btn { margin-left: auto; }
}
@media (max-width: 960px) {
  .hero { grid-template-columns: 1fr; padding-top: 40px; }
  .features { grid-template-columns: repeat(2, 1fr); }
  .model { grid-template-columns: 1fr; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .stat:nth-child(3) { border-left: none; }
}
@media (max-width: 560px) {
  .features { grid-template-columns: 1fr; }
  .stat-value { font-size: 19px; }
  .section { padding-top: 52px; }
}
</style>
