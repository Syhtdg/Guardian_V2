// src/utils/alarm.js
// 경보음을 음원 파일 없이 Web Audio API 로 직접 만듭니다. (저작권 걱정 없음)
//   불  : 높낮이가 오르내리는 사이렌
//   연기: 짧게 두 번 울리는 경고음 반복
// 브라우저는 사용자가 화면을 한 번 클릭하기 전에는 소리를 막으므로, unlockAlarm() 을 클릭 때 불러 둡니다.

const MUTE_KEY = 'guardian:alarm-muted'
let ctx = null
let timer = null
let nodes = []

function audio () {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) return null
    ctx = new AC()
  }
  return ctx
}

export function isMuted () {
  try {
    return localStorage.getItem(MUTE_KEY) === '1'
  } catch {
    return false
  }
}

export function setMuted (muted) {
  try {
    localStorage.setItem(MUTE_KEY, muted ? '1' : '0')
  } catch { /* 저장 못 해도 이번 화면에서는 적용 */ }
  if (muted) stopAlarm()
}

/** 클릭 등 사용자 동작 안에서 불러야 이후 자동 경보가 소리 납니다. */
export function unlockAlarm () {
  const ac = audio()
  if (ac && ac.state === 'suspended') ac.resume()
}

function tone (ac, { freq, freqEnd, start, dur, type = 'square', volume = 0.12 }) {
  const osc = ac.createOscillator()
  const gain = ac.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, start)
  if (freqEnd) osc.frequency.linearRampToValueAtTime(freqEnd, start + dur)
  gain.gain.setValueAtTime(0, start)
  gain.gain.linearRampToValueAtTime(volume, start + 0.02)
  gain.gain.setValueAtTime(volume, start + dur - 0.03)
  gain.gain.linearRampToValueAtTime(0, start + dur)
  osc.connect(gain).connect(ac.destination)
  osc.start(start)
  osc.stop(start + dur + 0.01)
  nodes.push(osc)
  osc.onended = () => { nodes = nodes.filter(n => n !== osc) }
}

function playPattern (ac, kind) {
  const t = ac.currentTime + 0.02
  if (kind === 'fire') {
    tone(ac, { freq: 650, freqEnd: 1250, start: t, dur: 0.5, type: 'sawtooth', volume: 0.09 })
    tone(ac, { freq: 1250, freqEnd: 650, start: t + 0.5, dur: 0.5, type: 'sawtooth', volume: 0.09 })
  } else {
    tone(ac, { freq: 880, start: t, dur: 0.16 })
    tone(ac, { freq: 880, start: t + 0.26, dur: 0.16 })
  }
}

/** kind: 'fire' | 'smoke'. 이미 울리고 있으면 겹쳐서 재생하지 않습니다. 반환값: 실제로 소리가 났는지 */
export function startAlarm (kind) {
  if (isMuted()) return false
  if (timer) return true
  const ac = audio()
  if (!ac) return false
  if (ac.state === 'suspended') ac.resume()
  playPattern(ac, kind)
  timer = setInterval(() => playPattern(ac, kind), kind === 'fire' ? 1000 : 1200)
  return ac.state === 'running'
}

export function stopAlarm () {
  clearInterval(timer)
  timer = null
  nodes.forEach(n => { try { n.stop() } catch { /* 이미 끝남 */ } })
  nodes = []
}
