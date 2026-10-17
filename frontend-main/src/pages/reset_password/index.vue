<template>
  <AuthShell title="비밀번호 재설정" icon="mdi-lock-reset" :subtitle="step === 1 ? '아이디와 가입한 이메일을 입력하면 6자리 인증코드를 보내 드립니다.' : info">
    <!-- 단계 표시 -->
    <div class="steps">
      <div class="step" :class="{ 'step--on': step >= 1 }"><span>1</span> 인증코드 받기</div>
      <div class="step-line" />
      <div class="step" :class="{ 'step--on': step >= 2 }"><span>2</span> 새 비밀번호</div>
    </div>

    <!-- 1단계: 아이디 + 이메일 → 인증코드 받기 -->
    <v-form v-if="step === 1" @submit.prevent="requestCode">
      <v-text-field v-model="ID" label="아이디" prepend-inner-icon="mdi-account-outline" class="mb-2" />
      <v-text-field v-model="EMAIL" label="이메일" type="email" prepend-inner-icon="mdi-email-outline" class="mb-4" />
      <v-btn type="submit" block size="large" color="primary" :loading="loading" prepend-icon="mdi-email-fast-outline">
        인증코드 받기
      </v-btn>
    </v-form>

    <!-- 2단계: 인증코드 + 새 비밀번호 -->
    <v-form v-else @submit.prevent="resetPassword">
      <v-text-field
        v-model="code"
        label="인증코드 (6자리)"
        prepend-inner-icon="mdi-numeric"
        maxlength="6"
        inputmode="numeric"
        class="mb-2"
      />
      <v-text-field
        v-model="newPassword"
        label="새 비밀번호"
        prepend-inner-icon="mdi-lock-outline"
        hint="영문과 숫자를 섞어 8자 이상"
        :type="showPassword ? 'text' : 'password'"
        :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
        class="mb-2"
        @click:append-inner="showPassword = !showPassword"
      />
      <v-text-field
        v-model="confirmPassword"
        label="새 비밀번호 확인"
        prepend-inner-icon="mdi-lock-check-outline"
        :type="showPassword ? 'text' : 'password'"
        class="mb-4"
      />
      <v-btn type="submit" block size="large" color="primary" :loading="loading">비밀번호 변경</v-btn>
      <v-btn block variant="text" class="mt-2" :disabled="loading" @click="requestCode">인증코드 다시 받기</v-btn>
    </v-form>

    <div class="auth-links">
      <router-link to="/find_ID">아이디 찾기</router-link>
      <span class="sep">|</span>
      <router-link to="/login">로그인</router-link>
    </div>
  </AuthShell>
</template>

<script>
import axios from '@/plugins/axios'
import AuthShell from '@/components/AuthShell.vue'

export default {
  components: { AuthShell },
  data () {
    return {
      step: 1,
      ID: '',
      EMAIL: '',
      code: '',
      newPassword: '',
      confirmPassword: '',
      showPassword: false,
      loading: false,
      info: ''
    }
  },
  methods: {
    async requestCode () {
      if (!this.ID || !this.EMAIL) {
        alert('아이디와 이메일을 입력해 주세요.')
        return
      }
      this.loading = true
      try {
        const res = await axios.post('/password/code', { ID: this.ID, EMAIL: this.EMAIL })
        this.info = res.data.message
        this.step = 2
      } catch (err) {
        alert(err.response?.data?.message || '인증코드 요청 실패')
      } finally {
        this.loading = false
      }
    },
    async resetPassword () {
      if (!/^\d{6}$/.test(this.code)) {
        alert('6자리 인증코드를 입력해 주세요.')
        return
      }
      if (this.newPassword !== this.confirmPassword) {
        alert('새 비밀번호가 서로 다릅니다.')
        return
      }
      this.loading = true
      try {
        const res = await axios.post('/password/reset', {
          ID: this.ID,
          EMAIL: this.EMAIL,
          code: this.code,
          newPassword: this.newPassword
        })
        alert(res.data.message)
        this.$router.push('/login')
      } catch (err) {
        alert(err.response?.data?.message || '비밀번호 변경 실패')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.steps {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}
.step {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.step span {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  font-weight: 600;
}
.step--on { color: #fff; }
.step--on span { background: #e53935; }
.step-line {
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.15);
}
.auth-links {
  margin-top: 18px;
  text-align: center;
  font-size: 13px;
}
.auth-links a {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
}
.auth-links a:hover { color: #ff6b66; }
.sep {
  margin: 0 10px;
  color: rgba(255, 255, 255, 0.25);
}
</style>
