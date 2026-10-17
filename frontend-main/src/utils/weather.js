// src/utils/weather.js
// Open-Meteo(키 없이 쓰는 무료 날씨 API)에서 현재 날씨를 가져옵니다.
// 같은 좌표는 10분 동안 다시 요청하지 않고 저장해 둔 값을 씁니다.

const CACHE_MS = 10 * 60 * 1000
const cache = new Map()

export async function fetchWeather (lat, lng) {
  const key = `${lat.toFixed(3)},${lng.toFixed(3)}`
  const hit = cache.get(key)
  if (hit && Date.now() - hit.at < CACHE_MS) return hit.data

  const url = 'https://api.open-meteo.com/v1/forecast' +
    `?latitude=${lat}&longitude=${lng}` +
    '&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation' +
    '&wind_speed_unit=ms&timezone=Asia%2FSeoul'

  const res = await fetch(url)
  if (!res.ok) throw new Error(`날씨 API 오류 (${res.status})`)
  const { current } = await res.json()

  const data = {
    temperature: current.temperature_2m,
    humidity: current.relative_humidity_2m,
    wind: current.wind_speed_10m,
    rain: current.precipitation,
    updatedAt: new Date(current.time)
  }
  cache.set(key, { at: Date.now(), data })
  return data
}
