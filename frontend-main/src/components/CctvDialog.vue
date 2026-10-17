<template>
  <v-dialog :model-value="modelValue" max-width="760" @update:model-value="$emit('update:modelValue', $event)">
    <v-card v-if="cctv" class="cctv-card">
      <div class="cctv-head">
        <div>
          <div class="cctv-title"><v-icon icon="mdi-cctv" class="mr-2" color="info" />{{ cctv.name }}</div>
          <div class="cctv-sub">
            {{ cctv.road ? `${cctv.road} · ` : '' }}{{ cctv.source || '실시간 영상' }}
            <span v-if="hasCoords"> · {{ cctv.lat.toFixed(5) }}, {{ cctv.lng.toFixed(5) }}</span>
          </div>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="$emit('update:modelValue', false)" />
      </div>

      <div class="px-5">
        <LiveStream :url="cctv.url" />
      </div>

      <!-- 이 CCTV 를 AI 로 감시: 감지기가 영상을 직접 분석하고, 불·연기가 나면 이 위치로 경보 -->
      <div v-if="showCommand" class="pa-5">
        <div class="cmd-title"><v-icon icon="mdi-robot-outline" size="18" class="mr-1" />이 CCTV 를 AI 로 감시하기</div>
        <p class="cmd-desc">
          아래 명령을 <code>ai</code> 폴더에서 실행하면 감지기가 이 영상을 분석합니다. 불·연기가 확인되면 이 CCTV 위치로 경보가 오고,
          경보 창에서 바로 실시간 영상을 볼 수 있습니다. 영상 주소에는 유효 시간이 있어 시간이 지나면 다시 복사해야 할 수 있습니다.
        </p>
        <div class="cmd-box">
          <code>{{ command }}</code>
          <v-btn size="small" variant="tonal" :prepend-icon="copied ? 'mdi-check' : 'mdi-content-copy'" @click="copy">
            {{ copied ? '복사됨' : '복사' }}
          </v-btn>
        </div>
      </div>
      <div v-else class="pa-3" />
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import LiveStream from '@/components/LiveStream.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // { id, name, lat, lng, url, road, source }
  cctv: { type: Object, default: null },
  showCommand: { type: Boolean, default: true }
})
defineEmits(['update:modelValue'])

const copied = ref(false)
watch(() => props.cctv, () => { copied.value = false })

const hasCoords = computed(() => typeof props.cctv?.lat === 'number' && typeof props.cctv?.lng === 'number')
const q = s => `"${String(s).replace(/"/g, '\\"')}"`
const command = computed(() => {
  const c = props.cctv
  if (!c) return ''
  let cmd = `python detect.py --source ${q(c.url)} --camera-id ${q(`cctv-${c.id}`)} --location ${q(c.name)}`
  if (hasCoords.value) cmd += ` --lat ${c.lat} --lng ${c.lng}`
  return cmd + ' --no-show'
})

async function copy () {
  try {
    await navigator.clipboard.writeText(command.value)
    copied.value = true
  } catch {
    alert('복사하지 못했습니다. 명령을 직접 선택해서 복사하세요.')
  }
}
</script>

<style scoped>
.cctv-card { border: 1px solid rgba(78, 168, 255, 0.25); }
.cctv-head { display: flex; justify-content: space-between; align-items: flex-start; padding: 16px 12px 12px 20px; }
.cctv-title { display: flex; align-items: center; font-size: 18px; font-weight: 700; }
.cctv-sub { margin-top: 4px; font-size: 12px; color: rgba(255, 255, 255, 0.55); }
.cmd-title { display: flex; align-items: center; font-weight: 600; margin-bottom: 6px; }
.cmd-desc { font-size: 12.5px; line-height: 1.6; color: rgba(255, 255, 255, 0.6); margin-bottom: 10px; }
.cmd-box { display: flex; gap: 10px; align-items: center; background: #0b0d10; border-radius: 8px; padding: 10px 12px; }
.cmd-box code { flex: 1; font-size: 12px; color: #9fe3c0; word-break: break-all; }
</style>
