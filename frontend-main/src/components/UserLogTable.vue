<template>
  <v-data-table
    :headers="headers"
    :items="logs"
    :loading="loading"
    :search="search"
    :items-per-page="15"
    hover
    class="log-table"
    no-data-text="기록이 없습니다."
    loading-text="불러오는 중..."
  >
    <template #item.action="{ item }">
      <v-chip size="small" variant="tonal" :color="ACTIONS[item.action]?.color || 'grey'" :prepend-icon="ACTIONS[item.action]?.icon">
        {{ ACTIONS[item.action]?.label || item.action }}
      </v-chip>
    </template>
    <template #item.timestamp="{ item }">
      {{ new Date(item.timestamp).toLocaleString('ko-KR') }}
    </template>
  </v-data-table>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/plugins/axios'

defineProps({ search: { type: String, default: '' } })

const logs = ref([])
const loading = ref(false)

const ACTIONS = {
  login: { label: '로그인', color: 'success', icon: 'mdi-login' },
  login_failed: { label: '로그인 실패', color: 'error', icon: 'mdi-account-alert-outline' },
  register: { label: '회원가입', color: 'info', icon: 'mdi-account-plus-outline' },
  find_id: { label: '아이디 찾기', color: 'secondary', icon: 'mdi-account-search-outline' },
  reset_code_sent: { label: '인증코드 발송', color: 'warning', icon: 'mdi-email-fast-outline' },
  password_reset: { label: '비밀번호 변경', color: 'warning', icon: 'mdi-lock-reset' }
}

const headers = [
  { title: '사용자 ID', key: 'userId' },
  { title: '행동', key: 'action' },
  { title: '세부내용', key: 'details' },
  { title: 'IP', key: 'ip' },
  { title: '기록 시각', key: 'timestamp' }
]

onMounted(async () => {
  loading.value = true
  try {
    const res = await axios.get('/log/all')
    logs.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.log-table { background: transparent; }
</style>
