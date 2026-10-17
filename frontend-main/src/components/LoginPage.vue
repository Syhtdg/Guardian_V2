<template>
  <div class="login-bg">
    <v-card class="login-box" elevation="12">
      <div class="left">
        <h1 class="title">로그인</h1>
        <p class="subtitle">관제 시스템에 접속합니다.</p>

        <v-alert v-if="expired" type="warning" variant="tonal" density="compact" class="mb-4">
          로그인이 만료되었습니다. 다시 로그인해 주세요.
        </v-alert>

        <v-form @submit.prevent="handleLogin">
          <v-text-field
            v-model="ID"
            label="아이디"
            prepend-inner-icon="mdi-account-outline"
            autocomplete="username"
            class="mb-2"
          />
          <v-text-field
            v-model="PASSWORD"
            label="비밀번호"
            prepend-inner-icon="mdi-lock-outline"
            :append-inner-icon="visible ? 'mdi-eye' : 'mdi-eye-off'"
            :type="visible ? 'text' : 'password'"
            autocomplete="current-password"
            class="mb-4"
            @click:append-inner="visible = !visible"
          />
          <v-btn type="submit" block size="large" color="primary" :loading="loading">로그인</v-btn>
        </v-form>

        <div class="links">
          <router-link to="/find_ID">아이디 찾기</router-link>
          <span class="sep">|</span>
          <router-link to="/reset_password">비밀번호 찾기</router-link>
          <span class="sep">|</span>
          <router-link to="/signup">회원가입</router-link>
        </div>
      </div>

      <div class="right">
        <img src="@/assets/right_side_logo.png" alt="Guardian" class="logo" />
        <div class="copy">
          <p class="copy-ko">
            <span class="hl">AI</span>를 활용한 시스템을 통해<br />
            누구보다 <span class="hl">빠르게</span> 화재를 감지하세요
          </p>
          <p class="copy-en">Detect fire faster than anyone else<br />with a system that uses AI</p>
        </div>
        <ul class="points">
          <li><v-icon icon="mdi-fire-alert" size="18" class="mr-2" />불·연기 실시간 감지와 경보</li>
          <li><v-icon icon="mdi-map-marker-radius-outline" size="18" class="mr-2" />지도에서 위치 확인</li>
          <li><v-icon icon="mdi-camera-outline" size="18" class="mr-2" />감지 순간 스냅샷 기록</li>
        </ul>
      </div>
    </v-card>
  </div>
</template>

<script>
import axios from '@/plugins/axios'
import { setToken } from '@/utils/auth'

export default {
  data () {
    return {
      ID: '',
      PASSWORD: '',
      visible: false,
      expired: this.$route.query.expired === '1',
      loading: false
    }
  },
  methods: {
    async handleLogin () {
      if (this.loading) return
      if (!this.ID || !this.PASSWORD) {
        alert('아이디와 비밀번호를 입력해 주세요.')
        return
      }
      this.loading = true
      try {
        const response = await axios.post('/login', {
          ID: this.ID,
          PASSWORD: this.PASSWORD
        })

        if (response.data.token) {
          setToken(response.data.token)
          // 로그인 전에 가려던 화면이 있으면 그쪽으로 (외부 주소는 무시)
          const redirect = this.$route.query.redirect
          const safe = typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')
          this.$router.push(safe ? redirect : '/dashboard')
        } else {
          alert('로그인 실패: 토큰 없음')
        }
      } catch (error) {
        alert('로그인 실패: ' + (error.response?.data?.message || '서버에 연결할 수 없습니다.'))
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-bg {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background:
    linear-gradient(rgba(10, 10, 12, 0.55), rgba(10, 10, 12, 0.7)),
    url('@/assets/login_bg.png') no-repeat center / cover;
}
.login-box {
  display: flex;
  width: 100%;
  max-width: 980px;
  overflow: hidden;
  background: rgba(24, 27, 33, 0.82) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.left, .right { flex: 1; padding: 44px 40px; }
.right {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 26px;
  background: linear-gradient(160deg, rgba(163, 5, 5, 0.28), rgba(0, 0, 0, 0.1));
  border-left: 1px solid rgba(255, 255, 255, 0.06);
}
.title { font-size: 28px; font-weight: 600; }
.subtitle { margin: 4px 0 26px; font-size: 14px; color: rgba(255, 255, 255, 0.6); }
.links { margin-top: 22px; text-align: center; font-size: 13px; }
.links a { color: rgba(255, 255, 255, 0.7); text-decoration: none; }
.links a:hover { color: #ff6b66; }
.sep { margin: 0 10px; color: rgba(255, 255, 255, 0.25); }
.logo { width: 240px; max-width: 100%; height: auto; }
.copy-ko { font-size: 17px; line-height: 1.7; color: rgba(255, 255, 255, 0.9); }
.copy-en { margin-top: 10px; font-size: 13px; line-height: 1.6; color: rgba(255, 255, 255, 0.55); letter-spacing: 0.3px; }
.hl { color: #ff5a4f; font-weight: 600; }
.points { list-style: none; padding: 0; font-size: 14px; color: rgba(255, 255, 255, 0.75); }
.points li { display: flex; align-items: center; padding: 5px 0; }

@media (max-width: 800px) {
  .login-box { flex-direction: column-reverse; max-width: 460px; }
  .left, .right { padding: 28px 24px; }
  .right { border-left: none; border-bottom: 1px solid rgba(255, 255, 255, 0.06); gap: 14px; }
  .logo { width: 170px; }
  .points { display: none; }
}
</style>
