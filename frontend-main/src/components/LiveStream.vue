<template>
  <!-- HLS(.m3u8) 실시간 영상. Chrome 등은 hls.js, Safari 는 브라우저 기본 재생을 씁니다 -->
  <div class="live">
    <video ref="video" class="live-video" muted playsinline autoplay controls />
    <div v-if="state !== 'playing'" class="live-overlay">
      <v-progress-circular v-if="state === 'loading'" indeterminate color="primary" />
      <template v-else>
        <img :src="noSignal" alt="" width="150" />
        <p class="live-msg">{{ message }}</p>
      </template>
    </div>
    <span v-if="state === 'playing'" class="live-badge"><span class="dot" />LIVE</span>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import Hls from 'hls.js'
import noSignal from '@/assets/illust/no-signal.svg'

const props = defineProps({ url: { type: String, default: '' } })

const video = ref(null)
const state = ref('loading') // loading | playing | error
const message = ref('')
let hls = null

function fail (msg) {
  state.value = 'error'
  message.value = msg
  destroy()
}

function explain (data) {
  const code = data?.response?.code
  if (code === 401 || code === 403) return '영상 주소가 만료되었거나 인증에 실패했습니다. (시험 키의 영상은 재생되지 않습니다)'
  if (code === 404) return '영상을 찾을 수 없습니다. CCTV 가 점검 중일 수 있습니다.'
  if (location.protocol === 'https:' && props.url.startsWith('http:')) return '보안 연결(https) 페이지에서는 http 영상을 재생할 수 없습니다.'
  return '영상을 불러오지 못했습니다. 잠시 후 다시 시도하세요.'
}

function destroy () {
  if (hls) { hls.destroy(); hls = null }
}

function load () {
  destroy()
  state.value = 'loading'
  const el = video.value
  if (!el || !props.url) return fail('영상 주소가 없습니다.')
  el.onplaying = () => { state.value = 'playing' }

  if (Hls.isSupported()) {
    hls = new Hls({ lowLatencyMode: true, manifestLoadingMaxRetry: 1 })
    hls.on(Hls.Events.ERROR, (_e, data) => { if (data.fatal) fail(explain(data)) })
    hls.loadSource(props.url)
    hls.attachMedia(el)
    hls.on(Hls.Events.MANIFEST_PARSED, () => el.play().catch(() => {}))
  } else if (el.canPlayType('application/vnd.apple.mpegurl')) {
    el.src = props.url
    el.onerror = () => fail(explain())
    el.play().catch(() => {})
  } else {
    fail('이 브라우저는 실시간 영상(HLS)을 재생할 수 없습니다.')
  }
}

watch(() => props.url, load)
onMounted(load)
onBeforeUnmount(destroy)
</script>

<style scoped>
.live { position: relative; width: 100%; aspect-ratio: 16 / 9; background: #0b0d10; border-radius: 10px; overflow: hidden; }
.live-video { width: 100%; height: 100%; object-fit: contain; display: block; }
.live-overlay { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; padding: 16px; text-align: center; background: #0b0d10; }
.live-msg { font-size: 13px; color: rgba(255, 255, 255, 0.65); max-width: 360px; line-height: 1.6; }
.live-badge { position: absolute; top: 10px; left: 10px; display: flex; align-items: center; gap: 6px; padding: 3px 9px; border-radius: 6px; background: rgba(0, 0, 0, 0.6); font-size: 12px; font-weight: 700; color: #ff8a8a; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #ff4d4f; animation: blink 1.2s infinite; }
@keyframes blink { 50% { opacity: 0.3; } }
</style>
