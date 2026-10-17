<template>
  <div class="nf">
    <img :src="noSignal" alt="" width="260" />
    <h1>404</h1>
    <p>찾는 화면이 없습니다. 주소를 확인하거나 아래 버튼으로 이동하세요.</p>
    <div class="actions">
      <v-btn to="/" variant="outlined" prepend-icon="mdi-home-outline">소개 화면</v-btn>
      <v-btn to="/dashboard" color="primary" variant="flat" prepend-icon="mdi-monitor-dashboard">대시보드</v-btn>
    </div>
  </div>
</template>

<script setup>
import noSignal from '@/assets/illust/no-signal.svg'
</script>

<style scoped>
.nf {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
  text-align: center;
  background: #0f1115;
}
h1 { font-size: 56px; font-weight: 800; margin-top: 10px; }
p { color: rgba(255, 255, 255, 0.6); }
.actions { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; justify-content: center; }
</style>
