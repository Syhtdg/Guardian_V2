<template>
  <v-data-table
    :headers="headers"
    :items="logs"
    :loading="loading"
    :search="search"
    :items-per-page="10"
    hover
    class="log-table"
    no-data-text="감지 기록이 없습니다."
    loading-text="불러오는 중..."
  >
    <template #item.imageUrl="{ item }">
      <a v-if="item.imageUrl" :href="assetUrl(item.imageUrl)" target="_blank" rel="noopener" class="thumb">
        <SnapshotImage :src="assetUrl(item.imageUrl)" height="64px" />
      </a>
      <div v-else class="thumb"><SnapshotImage height="64px" /></div>
    </template>
    <template #item.type="{ item }">
      <v-chip
        size="small"
        variant="flat"
        :color="item.type === '불' ? 'fire' : 'smoke'"
        :prepend-icon="item.type === '불' ? 'mdi-fire' : 'mdi-weather-fog'"
      >
        {{ item.type }}
      </v-chip>
    </template>
    <template #item.confidence="{ item }">
      <div class="conf">
        <v-progress-linear :model-value="item.confidence" :color="item.type === '불' ? 'fire' : 'smoke'" height="6" rounded />
        <span>{{ item.confidence }}%</span>
      </div>
    </template>
    <template #item.timestamp="{ item }">
      {{ new Date(item.timestamp).toLocaleString('ko-KR') }}
    </template>
  </v-data-table>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/plugins/axios'
import { assetUrl } from '@/utils/auth'
import SnapshotImage from '@/components/SnapshotImage.vue'

defineProps({ search: { type: String, default: '' } })

const logs = ref([])
const loading = ref(false)

const headers = [
  { title: '스냅샷', key: 'imageUrl', sortable: false },
  { title: '종류', key: 'type' },
  { title: '신뢰도', key: 'confidence' },
  { title: '위치', key: 'location' },
  { title: '카메라', key: 'cameraId' },
  { title: '감지 시각', key: 'timestamp' }
]

onMounted(async () => {
  loading.value = true
  try {
    const res = await axios.get('/ai/result/all')
    logs.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.log-table { background: transparent; }
.thumb {
  display: block;
  width: 104px;
  margin: 6px 0;
}
.conf {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}
</style>
