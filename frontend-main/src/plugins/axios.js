// src/plugins/axios.js
import axios from 'axios'
import { API_URL, getToken, logout } from '@/utils/auth'

const instance = axios.create({
  baseURL: API_URL,
  timeout: 15000,
})

instance.interceptors.request.use(config => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 토큰이 만료되면 로그인 화면으로 보냅니다 (로그인 요청 자체의 401 은 제외)
instance.interceptors.response.use(
  res => res,
  err => {
    const url = err.config?.url || ''
    if (err.response?.status === 401 && !url.includes('/login')) {
      logout()
      if (window.location.pathname !== '/login') {
        window.location.assign('/login?expired=1')
      }
    }
    return Promise.reject(err)
  }
)

export default instance
