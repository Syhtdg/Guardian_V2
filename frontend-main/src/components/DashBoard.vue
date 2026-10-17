<template>
  <AppHeader>
    <template #status>
      <v-chip
        :color="socketConnected ? 'success' : 'grey'"
        variant="tonal"
        size="small"
        class="mr-1"
      >
        <span class="live-dot" :class="{ 'live-dot--on': socketConnected }" />
        {{ socketConnected ? '실시간 연결됨' : '연결 끊김' }}
      </v-chip>
      <v-btn
        :icon="muted ? 'mdi-volume-off' : 'mdi-volume-high'"
        :title="muted ? '경보음 꺼짐 (누르면 켜기)' : '경보음 켜짐 (누르면 끄기)'"
        variant="text"
        size="small"
        @click="toggleMute"
      />
    </template>
  </AppHeader>

  <div class="dash">
    <!-- 요약 -->
    <v-row dense class="mb-2">
      <v-col v-for="s in stats" :key="s.label" cols="6" md="3">
        <v-card class="stat-card" :class="`stat-card--${s.tone}`">
          <div class="stat-icon"><v-icon :icon="s.icon" size="22" /></div>
          <div>
            <div class="stat-label">{{ s.label }}</div>
            <div class="stat-value">{{ s.value }}</div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- 감지 목록 -->
      <v-col cols="12" md="5" lg="4">
        <v-card class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <v-icon icon="mdi-alarm-light-outline" color="primary" class="mr-2" />
              감지 기록
              <v-chip size="x-small" variant="tonal" class="ml-2">{{ filteredLogs.length }}</v-chip>
            </div>
          </div>

          <div class="filters">
            <v-btn-toggle v-model="typeFilter" mandatory density="compact" variant="outlined" divided color="primary">
              <v-btn value="전체">전체</v-btn>
              <v-btn value="불" prepend-icon="mdi-fire">불</v-btn>
              <v-btn value="연기" prepend-icon="mdi-weather-fog">연기</v-btn>
            </v-btn-toggle>

            <v-menu v-model="dateMenu" :close-on-content-click="false" location="bottom end">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  variant="outlined"
                  density="comfortable"
                  prepend-icon="mdi-calendar-month-outline"
                  :color="selectedDate ? 'primary' : undefined"
                >
                  {{ formattedDate || '날짜' }}
                </v-btn>
              </template>
              <v-card>
                <v-date-picker v-model="selectedDate" color="primary" hide-header @update:model-value="onDateSelected" />
                <v-card-actions>
                  <v-spacer />
                  <v-btn variant="text" @click="clearDate">전체 날짜</v-btn>
                </v-card-actions>
              </v-card>
            </v-menu>
          </div>

          <div class="log-list">
            <div v-if="filteredLogs.length === 0" class="empty">
              <img :src="emptyImg" alt="" width="140" />
              <p class="empty-title">감지 기록이 없습니다</p>
              <p class="empty-sub">선택한 조건에서 불·연기가 감지되지 않았습니다.</p>
            </div>

            <div
              v-for="log in filteredLogs"
              :key="log._id"
              class="log-item"
              :class="[log.type === '불' ? 'log-item--fire' : 'log-item--smoke', { 'log-item--active': selectedId === log._id }]"
              @click="selectLog(log)"
            >
              <div class="log-thumb">
                <SnapshotImage :src="assetUrl(log.imageUrl)" height="78px" />
              </div>
              <div class="log-body">
                <div class="d-flex align-center justify-space-between">
                  <v-chip
                    size="small"
                    variant="flat"
                    :color="log.type === '불' ? 'fire' : 'smoke'"
                    :prepend-icon="log.type === '불' ? 'mdi-fire' : 'mdi-weather-fog'"
                  >
                    {{ log.type }}
                  </v-chip>
                  <span class="log-time" :title="formatKoreanDate(log.timestamp)">{{ relativeTime(log.timestamp) }}</span>
                </div>
                <div class="log-location">
                  <v-icon icon="mdi-map-marker-outline" size="14" class="mr-1" />{{ log.location }}
                </div>
                <div class="log-meta">
                  <span v-if="log.cameraId"><v-icon icon="mdi-cctv" size="13" class="mr-1" />{{ log.cameraId }}</span>
                  <v-btn
                    v-if="log.streamUrl"
                    icon="mdi-play-circle-outline"
                    size="x-small"
                    variant="text"
                    color="info"
                    title="실시간 영상 보기"
                    @click.stop="openStream(log)"
                  />
                  <span class="conf">
                    <v-progress-linear
                      :model-value="log.confidence"
                      :color="log.type === '불' ? 'fire' : 'smoke'"
                      height="5"
                      rounded
                      class="conf-bar"
                    />
                    {{ log.confidence }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </v-card>
      </v-col>

      <!-- 지도 + 기상 -->
      <v-col cols="12" md="7" lg="8">
        <v-card class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <v-icon icon="mdi-map-outline" color="primary" class="mr-2" />
              감지 위치
            </div>
            <div class="d-flex align-center ga-2">
              <span class="text-caption text-medium-emphasis d-none d-lg-inline">카메라별 최근 감지 · 기록을 누르면 이동</span>
              <v-btn
                size="small"
                :variant="cctvOn ? 'flat' : 'tonal'"
                :color="cctvOn ? 'info' : undefined"
                prepend-icon="mdi-cctv"
                :loading="cctvLoading"
                title="국가교통정보센터 공공 CCTV 를 지도에 표시"
                @click="toggleCctv"
              >
                공공 CCTV<span v-if="cctvOn && cctvItems.length">&nbsp;{{ cctvItems.length }}</span>
              </v-btn>
            </div>
          </div>
          <div class="map-wrap">
            <div id="map" class="map" />
            <div v-if="cctvOn && cctvNote" class="cctv-note">
              <v-icon icon="mdi-information-outline" size="16" class="mr-1" />{{ cctvNote }}
            </div>
            <div v-if="mapError" class="map-error">
              <v-icon icon="mdi-map-marker-off-outline" size="36" class="mb-2" />
              {{ mapError }}
            </div>
          </div>
        </v-card>

        <v-card class="panel mt-4">
          <div class="panel-head">
            <div class="panel-title">
              <v-icon icon="mdi-weather-partly-cloudy" color="info" class="mr-2" />
              기상 정보
            </div>
            <v-chip size="x-small" variant="tonal" :color="weatherError ? 'error' : 'info'">{{ weatherNote }}</v-chip>
          </div>
          <v-row dense class="px-4 pb-4">
            <v-col v-for="w in weather" :key="w.label" cols="6" sm="3">
              <div class="weather-item">
                <v-icon :icon="w.icon" size="22" :color="w.color" />
                <div>
                  <div class="weather-label">{{ w.label }}</div>
                  <div class="weather-value">{{ w.value }}</div>
                </div>
              </div>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </div>

  <!-- 실시간 경고 -->
  <v-dialog v-model="alertDialog" persistent max-width="560">
    <v-card class="alert-card" :class="alertIsFire ? 'alert-card--fire' : 'alert-card--smoke'">
      <div class="alert-head">
        <v-icon :icon="alertIsFire ? 'mdi-fire-alert' : 'mdi-weather-fog'" size="34" class="alert-icon" />
        <div>
          <div class="alert-title">{{ alertTitle }}</div>
          <div class="alert-sub">즉시 현장을 확인하세요</div>
        </div>
      </div>

      <div class="pa-5">
        <SnapshotImage :src="alertImage" height="280px" fit="contain" />

        <div class="alert-details">
          <div v-for="d in alertDetails" :key="d.label" class="alert-row">
            <v-icon :icon="d.icon" size="18" class="mr-2 text-medium-emphasis" />
            <span class="alert-label">{{ d.label }}</span>
            <span class="alert-value">{{ d.value }}</span>
          </div>
        </div>

        <v-btn
          v-if="alertData?.streamUrl"
          block
          variant="tonal"
          color="info"
          prepend-icon="mdi-play-circle-outline"
          class="mb-3"
          @click="openStream(alertData)"
        >
          실시간 영상 보기
        </v-btn>
        <v-alert v-if="soundBlocked" type="info" variant="tonal" density="compact" class="mb-3">
          브라우저가 경보음을 막았습니다. 화면을 한 번 클릭해 두면 다음 경보부터 소리가 납니다.
        </v-alert>
        <v-btn block size="large" color="primary" variant="flat" prepend-icon="mdi-bell-off-outline" @click="closeAlert">
          확인 (경보 끄기)
        </v-btn>
      </div>
    </v-card>
  </v-dialog>

  <!-- 공공 CCTV · 감지 카메라 실시간 영상 -->
  <CctvDialog v-model="cctvDialog" :cctv="cctvSelected" :show-command="cctvShowCommand" />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from '@/plugins/axios'
import { io } from 'socket.io-client'
import { format, formatDistanceToNow, isToday } from 'date-fns'
import { ko } from 'date-fns/locale'
import { API_URL, getToken, logout, assetUrl } from '@/utils/auth'
import { fetchWeather } from '@/utils/weather'
import { startAlarm, stopAlarm, unlockAlarm, isMuted, setMuted } from '@/utils/alarm'
import AppHeader from '@/components/AppHeader.vue'
import SnapshotImage from '@/components/SnapshotImage.vue'
import CctvDialog from '@/components/CctvDialog.vue'
import markerCctv from '@/assets/illust/marker-cctv.svg'
import emptyImg from '@/assets/illust/empty-safe.svg'
import markerFire from '@/assets/illust/marker-fire.svg'
import markerSmoke from '@/assets/illust/marker-smoke.svg'

const router = useRouter()

const MAX_LOGS = 200
const KAKAO_KEY = import.meta.env.VITE_KAKAO_MAP_KEY
const MAP_CENTER = {
  lat: Number(import.meta.env.VITE_MAP_CENTER_LAT) || 35.9135,
  lng: Number(import.meta.env.VITE_MAP_CENTER_LNG) || 128.8125
}

// 기상 정보: 지도 중심 좌표의 현재 날씨(Open-Meteo). 10분마다 갱신
const weatherData = ref(null)
const weatherError = ref(false)
let weatherTimer = null

const weather = computed(() => {
  const w = weatherData.value
  const val = (v, unit) => (v === undefined || v === null ? '-' : `${v}${unit}`)
  return [
    { label: '온도', value: val(w?.temperature, '℃'), icon: 'mdi-thermometer', color: 'warning' },
    { label: '습도', value: val(w?.humidity, '%'), icon: 'mdi-water-percent', color: 'info' },
    { label: '풍속', value: val(w?.wind, 'm/s'), icon: 'mdi-weather-windy', color: 'secondary' },
    { label: '강수량', value: val(w?.rain, 'mm'), icon: 'mdi-weather-rainy', color: 'info' }
  ]
})
const weatherNote = computed(() => {
  if (weatherError.value) return '날씨를 불러오지 못했습니다'
  if (!weatherData.value) return '불러오는 중...'
  return `${format(weatherData.value.updatedAt, 'HH:mm')} 기준 · Open-Meteo`
})

async function loadWeather () {
  try {
    weatherData.value = await fetchWeather(MAP_CENTER.lat, MAP_CENTER.lng)
    weatherError.value = false
  } catch (e) {
    console.warn('날씨 불러오기 실패:', e)
    weatherError.value = !weatherData.value // 이전 값이 있으면 그대로 보여 줌
  }
}

// 다이얼로그 상태
const alertDialog = ref(false)
const alertData = ref(null)
const alertImage = ref('')

// 경보음 (Web Audio 로 합성, 음원 파일 없음)
const muted = ref(isMuted())
const soundBlocked = ref(false)

// 필터 및 로그
const logs = ref([])
const typeFilter = ref('전체')
const selectedDate = ref(null)
const formattedDate = ref('')
const dateMenu = ref(false)
const selectedId = ref(null)

const socketConnected = ref(false)
let socket = null

// "3분 전" 같은 상대 시간을 주기적으로 갱신
const now = ref(Date.now())
let tick = null

// 지도
const mapError = ref('')
let map = null
let markers = []

// 공공 CCTV (국가교통정보센터 ITS) — 서버가 키를 들고 대신 조회
const cctvOn = ref(false)
const cctvItems = ref([])
const cctvLoading = ref(false)
const cctvNote = ref('')
const cctvDialog = ref(false)
const cctvSelected = ref(null)
const cctvShowCommand = ref(true)
let cctvMarkers = []
let cctvTimer = null
const CCTV_MAX_LEVEL = 9 // 이보다 축소하면 범위가 넓어 조회하지 않음

const fetchLogs = async () => {
  try {
    const res = await axios.get('/ai/result/all', { params: { limit: MAX_LOGS } })
    logs.value = res.data
  } catch (e) {
    console.error('AI 로그 불러오기 실패:', e)
  }
}

const onDateSelected = (date) => {
  formattedDate.value = date ? format(date, 'yyyy-MM-dd') : ''
  dateMenu.value = false
}

const clearDate = () => {
  selectedDate.value = null
  formattedDate.value = ''
  dateMenu.value = false
}

const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    const matchesType = typeFilter.value === '전체' || log.type === typeFilter.value
    const matchesDate =
      !selectedDate.value ||
      format(new Date(log.timestamp), 'yyyy-MM-dd') === format(selectedDate.value, 'yyyy-MM-dd')
    return matchesType && matchesDate
  })
})

const stats = computed(() => {
  const today = logs.value.filter(l => isToday(new Date(l.timestamp)))
  const last = logs.value[0]
  return [
    { label: '오늘 감지', value: today.length, icon: 'mdi-alarm-light-outline', tone: 'red' },
    { label: '오늘 불', value: today.filter(l => l.type === '불').length, icon: 'mdi-fire', tone: 'orange' },
    { label: '오늘 연기', value: today.filter(l => l.type === '연기').length, icon: 'mdi-weather-fog', tone: 'grey' },
    { label: '최근 감지', value: last ? relativeTime(last.timestamp) : '-', icon: 'mdi-clock-outline', tone: 'blue' }
  ]
})

const formatKoreanDate = (date) => {
  return format(new Date(date), 'yyyy년 M월 d일 (eee) HH:mm:ss', { locale: ko })
}

function relativeTime (date) {
  if (now.value - new Date(date).getTime() < 60000) return '방금 전' // now 가 바뀌면 다시 계산
  return formatDistanceToNow(new Date(date), { addSuffix: true, locale: ko })
}

const alertIsFire = computed(() => alertData.value?.type === '불')
const alertTitle = computed(() => (alertIsFire.value ? '화재 감지' : '연기 감지'))
const alertDetails = computed(() => {
  const d = alertData.value
  if (!d) return []
  const rows = [
    { label: '위치', value: d.location, icon: 'mdi-map-marker-outline' },
    { label: '신뢰도', value: `${d.confidence}%`, icon: 'mdi-gauge' },
    { label: '시각', value: formatKoreanDate(d.timestamp), icon: 'mdi-clock-outline' }
  ]
  if (d.cameraId) rows.splice(1, 0, { label: '카메라', value: d.cameraId, icon: 'mdi-cctv' })
  return rows
})

function toggleMute () {
  muted.value = !muted.value
  setMuted(muted.value)
  if (!muted.value) unlockAlarm()
}

function closeAlert () {
  alertDialog.value = false
  stopAlarm()
}

function showAlert (data) {
  alertData.value = data
  alertImage.value = assetUrl(data.imageUrl)
  alertDialog.value = true

  // 브라우저가 소리를 막았으면(화면을 한 번도 클릭하지 않음) 팝업에 안내
  soundBlocked.value = !muted.value && !startAlarm(data.type === '불' ? 'fire' : 'smoke')
}

function connectSocket () {
  socket = io(API_URL, { auth: { token: getToken() } })

  socket.on('connect', () => { socketConnected.value = true })
  socket.on('disconnect', () => { socketConnected.value = false })
  socket.on('connect_error', (err) => {
    socketConnected.value = false
    if (err.message === 'unauthorized') {
      logout()
      router.push('/login?expired=1')
    }
  })

  socket.on('aiResult', (data) => {
    logs.value.unshift(data)
    if (logs.value.length > MAX_LOGS) logs.value.pop()
    showAlert(data)
    selectLog(data)
  })
}

function selectLog (log) {
  selectedId.value = log._id
  focusOnMap(log)
}

// ───────── 카카오 지도 ─────────

function loadKakao () {
  if (!KAKAO_KEY) {
    mapError.value = '카카오맵 키가 없습니다. frontend-main/.env 의 VITE_KAKAO_MAP_KEY 를 설정하세요.'
    return
  }
  if (window.kakao?.maps) {
    window.kakao.maps.load(initMap)
    return
  }
  const script = document.createElement('script')
  script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_KEY}&autoload=false`
  script.onload = () => window.kakao.maps.load(initMap)
  script.onerror = () => { mapError.value = '카카오맵을 불러오지 못했습니다. 키와 허용 도메인을 확인하세요.' }
  document.head.appendChild(script)
}

function initMap () {
  const { kakao } = window
  const container = document.getElementById('map')
  if (!container) return
  map = new kakao.maps.Map(container, {
    center: new kakao.maps.LatLng(MAP_CENTER.lat, MAP_CENTER.lng),
    level: 4
  })
  map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT)
  // 지도를 옮기거나 확대하면 그 범위의 공공 CCTV 를 다시 불러옴
  kakao.maps.event.addListener(map, 'idle', () => { if (cctvOn.value) scheduleCctv() })
  drawMarkers()
}

// ───────── 공공 CCTV ─────────

const CCTV_START_LEVEL = 7 // 켤 때 이보다 확대돼 있으면 주변 약 15km 가 보이게 축소

function toggleCctv () {
  cctvOn.value = !cctvOn.value
  if (!cctvOn.value) return clearCctv()
  // 너무 확대된 상태면 주변 CCTV 가 보이게 축소 (축소가 끝나면 idle 이벤트에서 불러옴)
  if (map && map.getLevel() < CCTV_START_LEVEL) map.setLevel(CCTV_START_LEVEL)
  else loadCctv()
}

function scheduleCctv () {
  clearTimeout(cctvTimer)
  cctvTimer = setTimeout(loadCctv, 400)
}

function clearCctv () {
  cctvMarkers.forEach(m => m.setMap(null))
  cctvMarkers = []
  cctvItems.value = []
  cctvNote.value = ''
}

async function loadCctv () {
  if (!map) {
    cctvNote.value = '지도가 준비되지 않았습니다.'
    return
  }
  if (map.getLevel() > CCTV_MAX_LEVEL) {
    // 범위가 넓으면 새로 조회하지 않고, 이미 표시한 마커는 그대로 둠
    cctvNote.value = cctvItems.value.length
      ? '지도를 더 확대하면 이 범위의 공공 CCTV 를 새로 불러옵니다.'
      : '지도를 더 확대하면 공공 CCTV 가 표시됩니다.'
    return
  }
  const b = map.getBounds()
  const sw = b.getSouthWest()
  const ne = b.getNorthEast()
  cctvLoading.value = true
  try {
    const { data } = await axios.get('/cctv/public', {
      params: { minX: sw.getLng(), maxX: ne.getLng(), minY: sw.getLat(), maxY: ne.getLat() }
    })
    if (!cctvOn.value) return
    cctvItems.value = data.items.map(it => ({ ...it, source: data.source }))
    drawCctv()
    if (data.testKey) {
      cctvNote.value = '시험 키 사용 중: ITS 가 주는 예시 목록(수도권)이 표시되며 영상은 재생되지 않습니다.'
      // 예시 목록이 지금 화면 밖에 있으면 그쪽으로 이동
      const inView = cctvItems.value.some(it => b.contain(new window.kakao.maps.LatLng(it.lat, it.lng)))
      if (!inView && cctvItems.value.length) {
        const bounds = new window.kakao.maps.LatLngBounds()
        cctvItems.value.forEach(it => bounds.extend(new window.kakao.maps.LatLng(it.lat, it.lng)))
        map.setBounds(bounds)
      }
    } else {
      cctvNote.value = cctvItems.value.length ? '' : '이 범위에는 공공 CCTV 가 없습니다. 지도를 옮겨 보세요.'
    }
  } catch (e) {
    const code = e.response?.data?.code
    cctvNote.value = e.response?.data?.message || '공공 CCTV 정보를 가져오지 못했습니다.'
    if (code !== 'TOO_WIDE') clearCctvMarkersOnly()
  } finally {
    cctvLoading.value = false
  }
}

function clearCctvMarkersOnly () {
  cctvMarkers.forEach(m => m.setMap(null))
  cctvMarkers = []
}

function drawCctv () {
  const { kakao } = window
  clearCctvMarkersOnly()
  const image = new kakao.maps.MarkerImage(markerCctv, new kakao.maps.Size(28, 28), { offset: new kakao.maps.Point(14, 14) })
  for (const it of cctvItems.value) {
    const marker = new kakao.maps.Marker({
      map,
      image,
      position: new kakao.maps.LatLng(it.lat, it.lng),
      title: `${it.name} (공공 CCTV)`,
      zIndex: 1
    })
    kakao.maps.event.addListener(marker, 'click', () => openCctv(it))
    cctvMarkers.push(marker)
  }
}

function openCctv (it) {
  cctvSelected.value = it
  cctvShowCommand.value = true
  cctvDialog.value = true
}

// 감지 기록에 영상 주소가 있으면(공공 CCTV 를 감시하던 감지기) 그 장소의 실시간 영상을 띄움
function openStream (log) {
  cctvSelected.value = {
    id: log.cameraId || 'stream',
    name: log.location,
    lat: log.latitude,
    lng: log.longitude,
    url: log.streamUrl,
    source: log.cameraId ? `감지 카메라 ${log.cameraId}` : '감지 카메라'
  }
  cctvShowCommand.value = false
  cctvDialog.value = true
}

function drawMarkers () {
  if (!map) return
  const { kakao } = window
  markers.forEach(m => m.setMap(null))
  markers = []

  // 같은 카메라(좌표)는 가장 최근 감지 하나만 표시
  const seen = new Set()
  for (const log of filteredLogs.value) {
    if (typeof log.latitude !== 'number' || typeof log.longitude !== 'number') continue
    const key = `${log.latitude},${log.longitude}`
    if (seen.has(key)) continue
    seen.add(key)

    // 불은 빨간 불꽃 핀, 연기는 회색 구름 핀
    const image = new kakao.maps.MarkerImage(
      log.type === '불' ? markerFire : markerSmoke,
      new kakao.maps.Size(40, 48),
      { offset: new kakao.maps.Point(20, 46) }
    )
    const marker = new kakao.maps.Marker({
      map,
      image,
      position: new kakao.maps.LatLng(log.latitude, log.longitude),
      title: `${log.type} - ${log.location}`
    })
    const color = log.type === '불' ? '#ff5a36' : '#6b7480'
    const info = new kakao.maps.InfoWindow({
      removable: true,
      content: `<div style="padding:8px 12px;font-size:13px;color:#111;line-height:1.5;min-width:160px">` +
        `<b style="color:${color}">● ${log.type === '불' ? '화재' : '연기'}</b> ${log.confidence}%<br>` +
        `${escapeHtml(log.location)}</div>`
    })
    kakao.maps.event.addListener(marker, 'click', () => info.open(map, marker))
    markers.push(marker)
  }
}

function focusOnMap (log) {
  if (!map || typeof log.latitude !== 'number' || typeof log.longitude !== 'number') return
  map.panTo(new window.kakao.maps.LatLng(log.latitude, log.longitude))
}

function escapeHtml (s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
}

watch(filteredLogs, drawMarkers)

onMounted(() => {
  fetchLogs()
  connectSocket()
  loadKakao()
  loadWeather()
  window.addEventListener('pointerdown', unlockAlarm) // 클릭 한 번이면 이후 경보음 허용
  weatherTimer = setInterval(loadWeather, 10 * 60 * 1000)
  tick = setInterval(() => { now.value = Date.now() }, 30000)
})

// 화면을 떠날 때 소켓을 닫아야 다시 들어왔을 때 알림이 두 번씩 뜨지 않습니다
onUnmounted(() => {
  socket?.disconnect()
  stopAlarm()
  window.removeEventListener('pointerdown', unlockAlarm)
  clearInterval(tick)
  clearInterval(weatherTimer)
  clearTimeout(cctvTimer)
})
</script>

<style scoped>
.dash {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

/* 요약 카드 */
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-card--red .stat-icon { background: rgba(229, 57, 53, 0.18); color: #ff6b66; }
.stat-card--orange .stat-icon { background: rgba(255, 90, 54, 0.18); color: #ff8a65; }
.stat-card--grey .stat-icon { background: rgba(154, 164, 178, 0.18); color: #c3cad4; }
.stat-card--blue .stat-icon { background: rgba(78, 168, 255, 0.18); color: #7cc0ff; }
.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
}

/* 패널 공통 */
.panel {
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 16px 18px 12px;
}
.panel-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

/* 필터 */
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: space-between;
  padding: 0 18px 12px;
}

/* 감지 목록 */
.log-list {
  height: 640px;
  overflow-y: auto;
  padding: 4px 12px 12px;
}
.log-list::-webkit-scrollbar { width: 6px; }
.log-list::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 6px; }
.empty {
  text-align: center;
  padding: 60px 0;
  color: rgba(255, 255, 255, 0.5);
}
.empty-title {
  margin-top: 12px;
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}
.empty-sub {
  margin-top: 4px;
  font-size: 12px;
}
.log-item {
  display: flex;
  gap: 12px;
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: #1f232a;
  border-left: 4px solid transparent;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
}
.log-item:hover { background: #262b33; transform: translateX(2px); }
.log-item--fire { border-left-color: #ff5a36; }
.log-item--smoke { border-left-color: #9aa4b2; }
.log-item--active { background: #2b2f38; box-shadow: 0 0 0 1px rgba(229, 57, 53, 0.5); }
.log-thumb {
  width: 116px;
  flex-shrink: 0;
}
.log-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.log-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  white-space: nowrap;
}
.log-location {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.log-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}
.conf {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}
.conf-bar { width: 60px; }

/* 지도 */
.map-wrap {
  position: relative;
  margin: 0 18px 18px;
}
.map {
  width: 100%;
  height: 520px;
  border-radius: 12px;
  overflow: hidden;
  background: #0b0d10;
}
.cctv-note {
  position: absolute;
  left: 12px;
  right: 60px;
  bottom: 12px;
  z-index: 2;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(15, 17, 21, 0.85);
  color: rgba(255, 255, 255, 0.85);
  font-size: 12.5px;
}
.map-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px;
  color: rgba(255, 255, 255, 0.55);
}

/* 기상 */
.weather-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #1f232a;
}
.weather-label { font-size: 12px; color: rgba(255, 255, 255, 0.55); }
.weather-value { font-size: 17px; font-weight: 600; }

/* 경고 */
.alert-card {
  overflow: hidden;
  border: 1px solid rgba(255, 90, 54, 0.5);
  box-shadow: 0 0 40px rgba(229, 57, 53, 0.35) !important;
}
.alert-card--smoke {
  border-color: rgba(154, 164, 178, 0.5);
  box-shadow: 0 0 40px rgba(154, 164, 178, 0.25) !important;
}
.alert-head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 22px;
  background: linear-gradient(90deg, #b71c1c, #e53935);
  animation: flash 1.2s ease-in-out infinite;
}
.alert-card--smoke .alert-head {
  background: linear-gradient(90deg, #3a4049, #5d6672);
}
.alert-icon { color: #fff; }
.alert-title { font-size: 22px; font-weight: 700; color: #fff; }
.alert-sub { font-size: 13px; color: rgba(255, 255, 255, 0.8); }
.alert-details {
  margin: 18px 0 20px;
  border-radius: 10px;
  background: #1f232a;
  padding: 6px 14px;
}
.alert-row {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 15px;
}
.alert-row:last-child { border-bottom: none; }
.alert-label { width: 64px; color: rgba(255, 255, 255, 0.55); }
.alert-value { flex: 1; font-weight: 500; }

@keyframes flash {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.25); }
}

/* 상단 실시간 표시 점 */
.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #888;
  margin-right: 6px;
  display: inline-block;
}
.live-dot--on {
  background: #2ecc71;
  box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7);
  animation: pulse 1.6s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
  70% { box-shadow: 0 0 0 7px rgba(46, 204, 113, 0); }
  100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
}

@media (max-width: 600px) {
  .dash { padding: 12px; }
  .log-list { height: auto; max-height: 520px; }
  .map { height: 360px; }
  .stat-card { padding: 12px; gap: 10px; }
  .stat-icon { width: 36px; height: 36px; }
  .stat-value { font-size: 18px; }
}
</style>
