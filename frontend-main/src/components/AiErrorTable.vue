<template>
  <v-data-table
    :headers="headers"
    :items="logs"
    :loading="loading"
    :search="search"
    :items-per-page="15"
    hover
    show-expand
    item-value="_id"
    class="log-table"
    no-data-text="오류 기록이 없습니다."
    loading-text="불러오는 중..."
  >
    <template #item.errorType="{ item }">
      <v-chip size="small" variant="tonal" color="error" prepend-icon="mdi-alert-circle-outline">
        {{ item.errorType }}
      </v-chip>
    </template>
    <template #item.timestamp="{ item }">
      {{ new Date(item.timestamp).toLocaleString('ko-KR') }}
    </template>
    <template #expanded-row="{ columns, item }">
      <tr>
        <td :colspan="columns.length">
          <pre v-if="item.rawData" class="raw">{{ JSON.stringify(item.rawData, null, 2) }}</pre>
          <span v-else class="text-medium-emphasis">전달된 원본 데이터가 없습니다.</span>
        </td>
      </tr>
    </template>
  </v-data-table>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/plugins/axios'

defineProps({ search: { type: String, default: '' } })

const logs = ref([])
const loading = ref(false)

const headers = [
  { title: '오류 유형', key: 'errorType' },
  { title: '메시지', key: 'message' },
  { title: '위치', key: 'location' },
  { title: '카메라', key: 'cameraId' },
  { title: '시간', key: 'timestamp' },
  { title: '', key: 'data-table-expand' }
]

onMounted(async () => {
  loading.value = true
  try {
    const res = await axios.get('/ai/error/all')
    logs.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.log-table { background: transparent; }
.raw {
  margin: 8px 0;
  padding: 12px;
  border-radius: 8px;
  background: #0b0d10;
  font-size: 12px;
  overflow-x: auto;
}
</style>
