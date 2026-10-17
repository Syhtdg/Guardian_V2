<template>
  <AuthShell
    title="아이디 찾기"
    icon="mdi-account-search-outline"
    subtitle="가입할 때 입력한 이름과 이메일을 넣으면, 그 이메일로 아이디를 보내 드립니다."
  >
    <v-form @submit.prevent="findID">
      <v-text-field v-model="NAME" label="이름" prepend-inner-icon="mdi-card-account-details-outline" class="mb-2" />
      <v-text-field v-model="EMAIL" label="이메일" type="email" prepend-inner-icon="mdi-email-outline" class="mb-4" />
      <v-btn type="submit" block size="large" color="primary" :loading="loading" prepend-icon="mdi-email-fast-outline">
        아이디 메일로 받기
      </v-btn>
    </v-form>

    <v-alert v-if="resultMessage" type="success" variant="tonal" density="compact" class="mt-4">
      {{ resultMessage }}
    </v-alert>

    <div class="auth-links">
      <router-link to="/reset_password">비밀번호 찾기</router-link>
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
      NAME: '',
      EMAIL: '',
      resultMessage: '',
      loading: false
    }
  },
  methods: {
    async findID () {
      if (!this.NAME || !this.EMAIL) {
        alert('이름과 이메일을 입력해 주세요.')
        return
      }
      this.loading = true
      try {
        const res = await axios.post('/findID', { NAME: this.NAME, EMAIL: this.EMAIL })
        this.resultMessage = res.data.message
      } catch (err) {
        alert(err.response?.data?.message || '아이디 찾기 실패')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
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
