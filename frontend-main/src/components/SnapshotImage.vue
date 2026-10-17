<template>
  <!-- 스냅샷이 없거나 파일이 지워졌으면 깨진 이미지 대신 안내를 보여 줍니다 -->
  <img
    v-if="src && !failed"
    :src="src"
    :alt="alt"
    class="snapshot"
    :style="{ height, objectFit: fit }"
    loading="lazy"
    @error="failed = true"
  />
  <div v-else class="snapshot snapshot--empty" :style="{ height }">
    <img :src="missingImg" alt="" class="missing-img" />
    <span class="missing-text">스냅샷 없음</span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import missingImg from '@/assets/illust/snapshot-missing.svg'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '감지 스냅샷' },
  height: { type: String, default: '140px' },
  fit: { type: String, default: 'cover' },
})

const failed = ref(false)
watch(() => props.src, () => { failed.value = false })
</script>

<style scoped>
.snapshot {
  display: block;
  width: 100%;
  border-radius: 10px;
  background: #0b0d10;
}
.snapshot--empty {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.missing-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.missing-text {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 6px;
  text-align: center;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}
</style>
