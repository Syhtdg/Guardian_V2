<template>
  <!-- 회원가입 · 아이디 찾기 · 비밀번호 재설정이 같이 쓰는 화면 틀 (로그인 화면과 같은 배경) -->
  <div class="auth-bg">
    <v-card class="auth-card" width="100%" max-width="440" elevation="12">
      <div class="auth-top">
        <v-btn icon="mdi-arrow-left" variant="text" size="small" to="/login" aria-label="로그인으로" />
        <img src="@/assets/right_side_logo.png" alt="Guardian" class="auth-logo" />
        <span style="width: 40px" />
      </div>
      <div class="auth-title">
        <v-icon :icon="icon" color="primary" size="22" class="mr-2" />
        {{ title }}
      </div>
      <p v-if="subtitle" class="auth-subtitle">{{ subtitle }}</p>
      <slot />
    </v-card>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: 'mdi-shield-account-outline' },
})
</script>

<style scoped>
.auth-bg {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background:
    linear-gradient(rgba(10, 10, 12, 0.7), rgba(10, 10, 12, 0.85)),
    url('@/assets/login_bg.png') no-repeat center / cover;
}
.auth-card {
  padding: 28px 32px 32px;
  background: rgba(24, 27, 33, 0.88) !important;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.auth-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.auth-logo {
  height: 36px;
  width: auto;
}
.auth-title {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 6px;
}
.auth-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 22px;
  line-height: 1.6;
}
</style>
