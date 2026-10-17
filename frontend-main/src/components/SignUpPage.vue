<template>
  <AuthShell title="회원가입" icon="mdi-account-plus-outline" subtitle="관제 시스템에 접속할 계정을 만듭니다.">
    <v-form @submit.prevent="submitForm">
      <v-text-field
        v-model="ID"
        label="아이디"
        prepend-inner-icon="mdi-account-outline"
        hint="영문·숫자 4~20자"
        class="mb-2"
      />
      <v-text-field
        v-model="PASSWORD"
        label="비밀번호"
        prepend-inner-icon="mdi-lock-outline"
        :append-inner-icon="visible ? 'mdi-eye' : 'mdi-eye-off'"
        :type="visible ? 'text' : 'password'"
        hint="영문과 숫자를 섞어 8자 이상"
        class="mb-2"
        @click:append-inner="visible = !visible"
      />
      <v-text-field v-model="EMAIL" label="이메일" type="email" prepend-inner-icon="mdi-email-outline" class="mb-2" />
      <v-text-field v-model="NAME" label="이름" prepend-inner-icon="mdi-card-account-details-outline" class="mb-4" />

      <v-btn type="submit" block size="large" color="primary" :loading="loading">가입하기</v-btn>
    </v-form>

    <div class="auth-links">
      이미 계정이 있나요? <router-link to="/login">로그인</router-link>
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
      visible: false,
      loading: false,
      ID: '',
      PASSWORD: '',
      EMAIL: '',
      NAME: ''
    }
  },
  methods: {
    async submitForm () {
      if (this.loading) return
      this.loading = true
      try {
        const res = await axios.post('/register', {
          ID: this.ID,
          PASSWORD: this.PASSWORD,
          EMAIL: this.EMAIL,
          NAME: this.NAME
        })
        alert(res.data.message || '회원가입 성공!')
        this.$router.push('/login')
      } catch (err) {
        alert(err.response?.data?.message || '회원가입 실패')
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
  color: rgba(255, 255, 255, 0.6);
}
.auth-links a {
  color: #ff6b66;
  text-decoration: none;
  margin-left: 4px;
}
</style>
