<template>
  <AppHeader />

  <div class="cam-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">
          <v-icon icon="mdi-cctv" color="primary" class="mr-2" />
          카메라 현황
        </h2>
        <p class="page-sub">감지 기록과 오류 기록으로 집계한 카메라별 현황입니다. (카메라 등록·실시간 접속 상태는 아직 지원하지 않습니다)</p>
      </div>
      <v-btn variant="tonal" prepend-icon="mdi-refresh" :loading="loading" @click="load">새로고침</v-btn>
    </div>

    <div v-if="!loading && cameras.length === 0" class="empty">
      <img :src="emptyImg" alt="" width="140" />
      <p class="empty-title">아직 기록된 카메라가 없습니다</p>
      <p class="empty-sub">감지기(<code>ai/detect.py</code>)가 감지 결과나 오류를 보내면 여기에 나타납니다.</p>
    </div>

    <v-row v-else>
      <v-col v-for="c in cameras" :key="c.id" cols="12" sm="6" lg="4">
        <v-card class="cam-card">
          <div class="cam-head">
            <div class="cam-name">
              <v-icon icon="mdi-cctv" class="mr-2" />{{ c.id }}
            </div>
            <v-chip size="small" variant="tonal" :color="c.recentError ? 'error' : 'success'"
                    :prepend-icon="c.recentError ? 'mdi-alert-circle-outline' : 'mdi-check-circle-outline'">
              {{ c.recentError ? '최근 24시간 오류 있음' : '최근 24시간 오류 없음' }}
            </v-chip>
          </div>

          <div class="cam-loc">
            <v-icon icon="mdi-map-marker-outline" size="16" class="mr-1" />{{ c.location || '위치 미지정' }}
          </div>

          <div class="cam-stats">
            <div><span class="num">{{ c.fire }}</span><span class="lab">불</span></div>
            <div><span class="num">{{ c.smoke }}</span><span class="lab">연기</span></div>
            <div><span class="num">{{ c.errors }}</span><span class="lab">오류</span></div>
          </div>

          <v-divider class="my-3" />
          <div class="cam-row">
            <span class="lab">마지막 감지</span>
            <span>{{ c.lastDetection ? `${c.lastType} · ${ago(c.lastDetection)}` : '없음' }}</span>
          </div>
          <div class="cam-row">
            <span class="lab">마지막 오류</span>
            <span :class="{ 'text-error': c.recentError }">{{ c.lastError ? `${c.lastErrorType} · ${ago(c.lastError)}` : '없음' }}</span>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { ko } from 'date-fns/locale'
import axios from '@/plugins/axios'
import AppHeader from '@/components/AppHeader.vue'
import emptyImg from '@/assets/illust/empty-safe.svg'

const results = ref([])
const errors = ref([])
const loading = ref(false)
const DAY = 24 * 60 * 60 * 1000

const ago = (t) => formatDistanceToNow(new Date(t), { addSuffix: true, locale: ko })

// 카메라 ID(없으면 위치)별로 감지·오류 기록을 묶어 집계
const cameras = computed(() => {
  const map = new Map()
  const get = (key, location) => {
    if (!map.has(key)) {
      map.set(key, { id: key, location, fire: 0, smoke: 0, errors: 0, lastDetection: null, lastType: '', lastError: null, lastErrorType: '', recentError: false })
    }
    const c = map.get(key)
    if (!c.location && location) c.location = location
    return c
  }
  for (const r of results.value) {
    const c = get(r.cameraId || r.location || '알 수 없음', r.location)
    if (r.type === '불') c.fire++
    else if (r.type === '연기') c.smoke++
    const t = new Date(r.timestamp)
    if (!c.lastDetection || t > new Date(c.lastDetection)) { c.lastDetection = r.timestamp; c.lastType = r.type }
  }
  for (const e of errors.value) {
    const c = get(e.cameraId || e.location || '알 수 없음', e.location)
    c.errors++
    const t = new Date(e.timestamp)
    if (!c.lastError || t > new Date(c.lastError)) { c.lastError = e.timestamp; c.lastErrorType = e.errorType }
  }
  const now = Date.now()
  for (const c of map.values()) c.recentError = !!c.lastError && now - new Date(c.lastError).getTime() < DAY
  // 오류가 있는 카메라를 먼저, 그다음 최근 감지 순
  return [...map.values()].sort((a, b) =>
    (b.recentError - a.recentError) || (new Date(b.lastDetection || 0) - new Date(a.lastDetection || 0)))
})

async function load () {
  loading.value = true
  try {
    const [r, e] = await Promise.all([
      axios.get('/ai/result/all', { params: { limit: 2000 } }),
      axios.get('/ai/error/all', { params: { limit: 500 } })
    ])
    results.value = r.data
    errors.value = e.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.cam-page { padding: 24px; max-width: 1600px; margin: 0 auto; }
.page-head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.page-title { display: flex; align-items: center; font-size: 22px; font-weight: 600; }
.page-sub { font-size: 13px; color: rgba(255, 255, 255, 0.55); margin-top: 4px; max-width: 640px; }
.cam-card { padding: 18px; border: 1px solid rgba(255, 255, 255, 0.06); height: 100%; }
.cam-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.cam-name { display: flex; align-items: center; font-size: 17px; font-weight: 600; }
.cam-loc { display: flex; align-items: center; margin: 8px 0 14px; font-size: 13px; color: rgba(255, 255, 255, 0.6); }
.cam-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.cam-stats > div { background: #1f232a; border-radius: 10px; padding: 10px; text-align: center; }
.num { display: block; font-size: 22px; font-weight: 700; }
.lab { font-size: 12px; color: rgba(255, 255, 255, 0.55); }
.cam-row { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; }
.empty { text-align: center; padding: 70px 0; color: rgba(255, 255, 255, 0.5); }
.empty-title { margin-top: 12px; font-size: 15px; font-weight: 600; color: rgba(255, 255, 255, 0.8); }
.empty-sub { margin-top: 4px; font-size: 12px; }
@media (max-width: 600px) { .cam-page { padding: 12px; } }
</style>
