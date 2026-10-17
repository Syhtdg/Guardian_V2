// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router/auto'
import { setupLayouts } from 'virtual:generated-layouts'
import { routes } from 'vue-router/auto-routes'
import { isLoggedIn } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: setupLayouts(routes),
})

// 로그인 없이 볼 수 있는 화면
const PUBLIC_PATHS = ['/', '/login', '/signup', '/find_ID', '/reset_password']

router.beforeEach(to => {
  const isPublic = PUBLIC_PATHS.includes(to.path.replace(/\/$/, '') || '/')
  const loggedIn = isLoggedIn()

  if (!isPublic && !loggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  // 이미 로그인했으면 로그인 화면 대신 대시보드로
  if (loggedIn && (to.path === '/' || to.path === '/login')) {
    return { path: '/dashboard' }
  }
})

router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (!localStorage.getItem('vuetify:dynamic-reload')) {
      console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    } else {
      console.error('Dynamic import error, reloading page did not fix it', err)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})

export default router
