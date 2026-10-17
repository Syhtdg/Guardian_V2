// src/utils/auth.js
// 로그인 토큰 저장/확인/삭제

const TOKEN_KEY = 'token'

export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:10111').replace(/\/$/, '')

export function getToken () {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken (token) {
  localStorage.setItem(TOKEN_KEY, token)
}

function decodePayload (token) {
  try {
    const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const json = decodeURIComponent(
      atob(part).split('').map(c => '%' + c.charCodeAt(0).toString(16).padStart(2, '0')).join('')
    )
    return JSON.parse(json)
  } catch {
    return null
  }
}

/** 토큰이 있고 만료되지 않았으면 true */
export function isLoggedIn () {
  const token = getToken()
  if (!token) return false
  const payload = decodePayload(token)
  return Boolean(payload && payload.exp * 1000 > Date.now())
}

export function currentUser () {
  const payload = decodePayload(getToken() || '')
  return payload ? { ID: payload.ID, NAME: payload.NAME } : null
}

export function logout () {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch { /* 무시 */ }
}

/** 서버에 저장된 스냅샷 경로(/snapshots/..)를 전체 주소로 */
export function assetUrl (path) {
  if (!path) return ''
  return /^https?:\/\//.test(path) ? path : API_URL + path
}
