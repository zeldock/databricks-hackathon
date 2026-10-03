// Tiny synthesized sound kit (Web Audio) — no audio files needed. Respects a persisted mute toggle.
import { useSyncExternalStore } from 'react'

let ctx: AudioContext | null = null
const KEY = 'wolf-tracks-muted'
let muted = (() => { try { return localStorage.getItem(KEY) === '1' } catch { return false } })()
const subs = new Set<() => void>()

export const isMuted = () => muted
export const setMuted = (m: boolean) => {
  muted = m
  try { localStorage.setItem(KEY, m ? '1' : '0') } catch { /* private mode */ }
  subs.forEach((f) => f())
}
export const useMuted = () => useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f) }, isMuted)

function ac(): AudioContext | null {
  if (muted) return null
  try {
    const W = window as unknown as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext }
    ctx ||= new (W.AudioContext || W.webkitAudioContext!)()
    if (ctx.state === 'suspended') void ctx.resume()
    return ctx
  } catch { return null }
}

type Tone = { f: number; d?: number; t?: number; type?: OscillatorType; v?: number; to?: number }
function play(tones: Tone[]) {
  const c = ac(); if (!c) return
  const now = c.currentTime
  for (const { f, d = 0.15, t = 0, type = 'sine', v = 0.14, to } of tones) {
    const o = c.createOscillator(), g = c.createGain()
    o.type = type; o.frequency.setValueAtTime(f, now + t)
    if (to) o.frequency.exponentialRampToValueAtTime(to, now + t + d)
    g.gain.setValueAtTime(0.0001, now + t)
    g.gain.exponentialRampToValueAtTime(v, now + t + 0.012)
    g.gain.exponentialRampToValueAtTime(0.0001, now + t + d)
    o.connect(g).connect(c.destination)
    o.start(now + t); o.stop(now + t + d + 0.05)
  }
}
const notes = (freqs: number[], step: number, o: Partial<Tone> = {}) => freqs.map((f, i) => ({ f, t: i * step, ...o }))

export const sfx = {
  click: () => play([{ f: 520, d: 0.05, type: 'triangle', v: 0.08 }]),
  tick: () => play([{ f: 1300, d: 0.03, type: 'square', v: 0.035 }]),
  thunk: () => play([{ f: 170, to: 70, d: 0.14, type: 'triangle', v: 0.22 }]),
  coin: () => play([{ f: 988, d: 0.07, type: 'square', v: 0.07 }, { f: 1319, t: 0.07, d: 0.22, type: 'square', v: 0.07 }]),
  buy: () => play([...notes([784, 988, 1175], 0.07, { type: 'triangle', d: 0.14 }), { f: 1568, t: 0.24, d: 0.3, type: 'triangle' }]),
  equip: () => play([{ f: 440, to: 880, d: 0.12, type: 'triangle' }]),
  claim: () => play(notes([523, 659, 784], 0.08, { type: 'triangle', d: 0.18 })),
  win: () => play(notes([523, 659, 784, 1047], 0.09, { type: 'triangle', d: 0.2 })),
  jackpot: () => play([...notes([523, 659, 784, 1047, 1319, 1568, 2093], 0.075, { type: 'square', v: 0.09, d: 0.2 }), { f: 1047, t: 0.6, d: 0.7, type: 'triangle', v: 0.12 }]),
  chest: () => play([{ f: 120, to: 90, d: 0.35, type: 'sawtooth', v: 0.1 }, ...notes([392, 523, 659, 784, 1047], 0.08, { t: 0.3, type: 'triangle', d: 0.25 } as Partial<Tone>)]),
  levelUp: () => play(notes([392, 494, 587, 784, 988], 0.1, { type: 'triangle', d: 0.3 })),
  oops: () => play([{ f: 330, to: 150, d: 0.35, type: 'sawtooth', v: 0.08 }]),
  pet: () => play([{ f: 660, to: 880, d: 0.12, type: 'sine' }, { f: 880, to: 1100, t: 0.1, d: 0.14, type: 'sine' }]),
}

/** Schedule decelerating wheel ticks that match an ease-out spin. Returns a cancel function. */
export function wheelTicks(durationMs: number, count: number): () => void {
  const timers: number[] = []
  for (let k = 1; k <= count; k++) {
    const t = (1 - Math.pow(1 - k / count, 1 / 3)) * durationMs
    timers.push(window.setTimeout(sfx.tick, t))
  }
  return () => timers.forEach(clearTimeout)
}
