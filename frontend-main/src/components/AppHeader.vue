<template>
  <v-app-bar flat height="64" class="app-header">
    <router-link to="/dashboard" class="brand">
      <img src="@/assets/logo_3d.png" alt="Guardian" class="brand-logo" />
    </router-link>

    <div class="nav d-none d-md-flex">
      <v-btn to="/dashboard" variant="text" prepend-icon="mdi-view-dashboard-outline">대시보드</v-btn>
      <v-btn to="/log" variant="text" prepend-icon="mdi-text-box-search-outline">로그 관리</v-btn>
      <v-btn to="/cameras" variant="text" prepend-icon="mdi-cctv">카메라 현황</v-btn>
    </div>

    <v-spacer />

    <slot name="status" />

    <v-menu location="bottom end">
      <template #activator="{ props }">
        <v-btn v-bind="props" variant="text" class="ml-2">
          <v-avatar color="primary" size="30" class="mr-2">
            <span class="text-caption font-weight-bold">{{ initial }}</span>
          </v-avatar>
          <span class="d-none d-sm-inline">{{ user?.NAME || '사용자' }}</span>
          <v-icon icon="mdi-chevron-down" size="18" class="ml-1" />
        </v-btn>
      </template>
      <v-list density="compact" min-width="180">
        <v-list-item :subtitle="user?.ID" :title="user?.NAME" />
        <v-divider />
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard-outline" title="대시보드" class="d-md-none" />
        <v-list-item to="/log" prepend-icon="mdi-text-box-search-outline" title="로그 관리" class="d-md-none" />
        <v-list-item to="/cameras" prepend-icon="mdi-cctv" title="카메라 현황" class="d-md-none" />
        <v-list-item prepend-icon="mdi-logout" title="로그아웃" @click="handleLogout" />
      </v-list>
    </v-menu>
  </v-app-bar>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, logout } from '@/utils/auth'

const router = useRouter()
const user = currentUser()
const initial = computed(() => (user?.NAME || user?.ID || '?').slice(0, 1).toUpperCase())

function handleLogout () {
  logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  background: linear-gradient(90deg, #7a0606 0%, #a30505 45%, #2a0a0a 100%) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.brand {
  display: flex;
  align-items: center;
  margin: 0 20px 0 16px;
}
.brand-logo {
  height: 34px;
  width: auto;
}
.nav :deep(.v-btn) {
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.85);
}
.nav :deep(.v-btn--active) {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}
</style>
