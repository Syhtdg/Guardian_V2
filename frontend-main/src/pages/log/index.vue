<template>
  <AppHeader />

  <div class="log-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">
          <v-icon icon="mdi-text-box-search-outline" color="primary" class="mr-2" />
          로그 통합 관리
        </h2>
        <p class="page-sub">사용자 활동, AI 감지 결과, AI 오류 기록을 확인합니다.</p>
      </div>
      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        placeholder="검색"
        density="compact"
        hide-details
        clearable
        class="search"
      />
    </div>

    <v-card class="panel">
      <v-tabs v-model="tab" color="primary" class="px-2">
        <v-tab :value="0" prepend-icon="mdi-account-clock-outline">사용자 로그</v-tab>
        <v-tab :value="1" prepend-icon="mdi-fire-alert">AI 감지 로그</v-tab>
        <v-tab :value="2" prepend-icon="mdi-alert-circle-outline">AI 에러 로그</v-tab>
      </v-tabs>
      <v-divider />

      <v-window v-model="tab">
        <v-window-item :value="0">
          <UserLogTable :search="search" />
        </v-window-item>
        <v-window-item :value="1">
          <AiResultTable :search="search" />
        </v-window-item>
        <v-window-item :value="2">
          <AiErrorTable :search="search" />
        </v-window-item>
      </v-window>
    </v-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import UserLogTable from '@/components/UserLogTable.vue'
import AiResultTable from '@/components/AiResultTable.vue'
import AiErrorTable from '@/components/AiErrorTable.vue'

const tab = ref(0)
const search = ref('')
</script>

<style scoped>
.log-page {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}
.page-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.page-title {
  display: flex;
  align-items: center;
  font-size: 22px;
  font-weight: 600;
}
.page-sub {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  margin-top: 4px;
}
.search {
  max-width: 320px;
  min-width: 220px;
}
.panel {
  border: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
