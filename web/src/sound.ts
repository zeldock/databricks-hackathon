// Synthesized sound kit (Web Audio) — no audio files. Four volume levels; INSANE is deliberately obnoxious.
import { useSyncExternalStore } from 'react'

export type Volume = 'off' | 'normal' | 'loud' | 'insane'
const ORDER: Volume[] = ['insane', 'loud', 'normal', 'off']
// master gain, soft-clip drive (adds crunch and perceived loudness), compressor threshold (dB)
const LEVELS: Record<Volume, { gain: number; drive: number; thr: number }> = {
  off: { gain: 0, drive: 1, thr: -10 },
  normal: { gain: 0.9, drive: 1.2, thr: -14 },
  loud: { gain: 1.8, drive: 3, thr: -22 },
  insane: { gain: 3.2, drive: 9, thr: -30 },
}

let ctx: AudioContext | null = null
let bus: AudioNode | null = null
let master: GainNode | null = null
let shaper: WaveShaperNode | null = null
let comp: DynamicsCompressorNode | null = null
const KEY = 'wolf-tracks-volume'
let volume: Volume = (() => {
  try {
    const v = localStorage.getItem(KEY) as Volume | null
    if (v && v in LEVELS) return v
    if (localStorage.getItem('wolf-tracks-muted') === '1') return 'off'
  } catch { /* storage unavailable */ }
  return 'insane'
})()
const subs = new Set<() => void>()

const curve = (drive: number) => {
  const n = 2048, c = new Float32Array(n)
  for (let i = 0; i < n; i++) { const x = (i / (n - 1)) * 2 - 1; c[i] = Math.tanh(x * drive) / Math.tanh(drive) }
  return c
}
function applyLevel() {
  if (!ctx || !master || !shaper || !comp) return
  const l = LEVELS[volume]
  master.gain.value = l.gain
  shaper.curve = curve(l.drive) as unknown as Float32Array<ArrayBuffer>
  comp.threshold.value = l.thr
}

export const getVolume = () => volume
export const isMuted = () => volume === 'off'
export const setVolume = (v: Volume) => {
  volume = v
  try { localStorage.setItem(KEY, v) } catch { /* private mode */ }
  applyLevel(); subs.forEach((f) => f())
}
export const cycleVolume = () => setVolume(ORDER[(ORDER.indexOf(volume) + 1) % ORDER.length])
export const setMuted = (m: boolean) => setVolume(m ? 'off' : 'insane')
export const useVolume = () => useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f) }, getVolume)
export const useMuted = () => useVolume() === 'off'

function ac(): AudioContext | null {
  if (volume === 'off') return null
  try {
    const W = window as unknown as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext }
    if (!ctx) {
      ctx = new (W.AudioContext || W.webkitAudioContext!)()
      master = ctx.createGain()
      shaper = ctx.createWaveShaper(); shaper.oversample = '2x'
      comp = ctx.createDynamicsCompressor()
      comp.knee.value = 6; comp.ratio.value = 20; comp.attack.value = 0.001; comp.release.value = 0.12
      const makeup = ctx.createGain(); makeup.gain.value = 1.15
      master.connect(shaper).connect(comp).connect(makeup).connect(ctx.destination)
      bus = master
      applyLevel()
    }
    if (ctx.state === 'suspended') void ctx.resume()
    return ctx
  } catch { return null }
}
const out = (c: AudioContext) => bus ?? c.destination
const rand = (a: number, b: number) => a + Math.random() * (b - a)

type Tone = { f: number; d?: number; t?: number; type?: OscillatorType; v?: number; to?: number; detune?: number }
function play(tones: Tone[]) {
  const c = ac(); if (!c) return
  const now = c.currentTime
  for (const { f, d = 0.15, t = 0, type = 'sine', v = 0.14, to, detune = 0 } of tones) {
    const o = c.createOscillator(), g = c.createGain()
    o.type = type; o.frequency.setValueAtTime(f, now + t); o.detune.value = detune
    if (to) o.frequency.exponentialRampToValueAtTime(to, now + t + d)
    g.gain.setValueAtTime(0.0001, now + t)
    g.gain.exponentialRampToValueAtTime(v, now + t + 0.012)
    g.gain.exponentialRampToValueAtTime(0.0001, now + t + d)
    o.connect(g).connect(out(c))
    o.start(now + t); o.stop(now + t + d + 0.05)
  }
}
const notes = (freqs: number[], step: number, o: Partial<Tone> = {}) => freqs.map((f, i) => ({ f, t: i * step, ...o }))

/* ------------------------------------------------------------- casino kit */
/** Bright metallic bell. `rich` adds all the inharmonic partials; the lite version is cheap for showers. */
function bell(freq: number, t = 0, v = 0.3, decay = 1.1, rich = true) {
  const c = ac(); if (!c) return
  const now = c.currentTime + t
  const partials = rich ? [[1, 1], [2.76, 0.55], [5.4, 0.32], [8.93, 0.18]] : [[1, 1], [2.76, 0.5]]
  partials.forEach(([ratio, amp]) => {
    const o = c.createOscillator(), g = c.createGain()
    o.type = 'sine'; o.frequency.value = freq * ratio
    g.gain.setValueAtTime(0.0001, now)
    g.gain.exponentialRampToValueAtTime(v * amp, now + 0.004)
    g.gain.exponentialRampToValueAtTime(0.0001, now + decay / ratio ** 0.35)
    o.connect(g).connect(out(c)); o.start(now); o.stop(now + decay + 0.05)
  })
}

type Filt = BiquadFilterType
function noise(t = 0, d = 0.05, v = 0.3, freq = 2000, q = 1, type: Filt = 'bandpass', sweepTo?: number) {
  const c = ac(); if (!c) return
  const now = c.currentTime + t
  const buf = c.createBuffer(1, Math.max(1, Math.floor(c.sampleRate * d)), c.sampleRate)
  const data = buf.getChannelData(0)
  for (let i = 0; i < data.length; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / data.length) ** (type === 'bandpass' ? 1 : 0.5)
  const src = c.createBufferSource(); src.buffer = buf
  const f = c.createBiquadFilter(); f.type = type; f.frequency.setValueAtTime(freq, now); f.Q.value = q
  if (sweepTo) f.frequency.exponentialRampToValueAtTime(sweepTo, now + d)
  const g = c.createGain(); g.gain.setValueAtTime(v, now); g.gain.exponentialRampToValueAtTime(0.0001, now + d)
  src.connect(f).connect(g).connect(out(c)); src.start(now)
}

/** Cash-register CHING: drawer clack + two bright bells + a high sparkle. */
function ching(t = 0, v = 0.6) {
  noise(t, 0.05, v, 3200, 0.8)
  bell(2349, t, v, 1.5); bell(3136, t + 0.06, v, 1.8); bell(4699, t + 0.11, v * 0.6, 1.0, false)
}
function coinShower(count: number, spanSec: number) {
  for (let i = 0; i < count; i++) {
    const t = (i / count) * spanSec + rand(0, 0.05)
    bell(rand(1500, 5200), t, rand(0.14, 0.3), rand(0.25, 0.55), false)
    if (i % 4 === 0) noise(t, 0.03, 0.2, rand(3000, 7000), 2)
  }
}
function siren(sec: number, v = 0.3, lo = 700, hi = 1500) {
  const c = ac(); if (!c) return
  const now = c.currentTime
  ;[0, 7].forEach((det) => {
    const o = c.createOscillator(), g = c.createGain()
    o.type = 'square'; o.detune.value = det * 6
    for (let i = 0; i * 0.38 < sec; i++) { o.frequency.setValueAtTime(lo, now + i * 0.38); o.frequency.linearRampToValueAtTime(hi, now + i * 0.38 + 0.36) }
    g.gain.setValueAtTime(v, now); g.gain.setValueAtTime(v, now + sec - 0.1); g.gain.exponentialRampToValueAtTime(0.0001, now + sec)
    o.connect(g).connect(out(c)); o.start(now); o.stop(now + sec + 0.05)
  })
}
/** Stadium air horn: stacked detuned saws with a sagging pitch. */
function horn(t = 0, d = 0.9, v = 0.3, base = 466) {
  ;[1, 1.26, 1.5].forEach((r, i) => [-14, 0, 14].forEach((det) => play([{ f: base * r * 1.04, to: base * r, t, d, type: 'sawtooth', v: v / 6, detune: det + i }])))
  play([{ f: base / 2, t, d, type: 'square', v: v / 3 }])
}
function fanfare(t = 0, v = 0.28) {
  const chord = (f: number[], at: number, d: number) => f.forEach((x) => play([{ f: x, t: at, d, type: 'sawtooth', v: v / f.length * 1.8 }, { f: x * 2, t: at, d, type: 'square', v: v / f.length * 0.6 }, { f: x / 2, t: at, d, type: 'triangle', v: v / f.length }]))
  chord([523, 659, 784], t, 0.2); chord([523, 659, 784], t + 0.22, 0.2); chord([587, 740, 880], t + 0.44, 0.2); chord([659, 831, 988, 1319], t + 0.66, 1.1)
}
/** Explosion: low-passed noise sweep + sub drop. */
function boom(t = 0, v = 0.9) {
  noise(t, 1.3, v, 1400, 0.7, 'lowpass', 50)
  play([{ f: 95, to: 28, t, d: 0.9, type: 'sine', v: v * 1.2 }, { f: 55, to: 25, t, d: 1.1, type: 'triangle', v: v }])
}
function crash(t = 0, v = 0.5) { noise(t, 2.2, v, 5500, 0.5, 'highpass'); noise(t, 1.0, v * 0.6, 9000, 0.4, 'highpass') }
/** Rising whoosh + pitch sweep that builds tension. */
function riser(sec: number, v = 0.4) {
  noise(0, sec, v, 300, 1.2, 'bandpass', 7000)
  play([{ f: 200, to: 2200, d: sec, type: 'sawtooth', v: v * 0.5 }, { f: 100, to: 1100, d: sec, type: 'square', v: v * 0.3 }])
}
/** Frantic arcade arpeggio. */
function arcade(sec: number, v = 0.22) {
  const scale = [523, 587, 659, 784, 880, 1047, 1175, 1319, 1568]
  const step = 0.075
  for (let i = 0; i < sec / step; i++) {
    const f = scale[(i * 3 + (i >> 2)) % scale.length] * (i % 8 > 4 ? 2 : 1)
    play([{ f, t: i * step, d: step * 1.3, type: 'square', v }, { f: f / 2, t: i * step, d: step * 1.3, type: 'triangle', v: v * 0.8 }])
  }
}

/** Snare-roll build-up that accelerates and crescendos. */
function snareRoll(sec: number, v = 0.5) {
  let t = 0, gap = 0.14
  while (t < sec) { noise(t, 0.09, v * (0.3 + 0.7 * (t / sec)), 2200 + 1800 * (t / sec), 0.8); t += gap; gap = Math.max(0.028, gap * 0.9) }
}
/** Four-on-the-floor dance beat with offbeat hats, claps and a pumping bass. */
function dance(sec: number, v = 0.5, bpm = 144) {
  const beat = 60 / bpm
  for (let i = 0; i < sec / beat; i++) {
    const t = i * beat
    play([{ f: 160, to: 42, t, d: 0.22, type: 'sine', v: v * 1.6 }])
    noise(t + beat / 2, 0.05, v * 0.5, 9000, 0.6, 'highpass')
    if (i % 2 === 1) { noise(t, 0.14, v * 0.8, 1500, 0.7); noise(t, 0.09, v * 0.5, 3500, 0.9) }
    play([{ f: [55, 55, 82, 73][i % 4], t: t + beat / 2, d: beat * 0.45, type: 'sawtooth', v: v * 0.5 }])
  }
}
/** A wolf howl: rising/falling pitch with vibrato. */
function howl(t = 0, v = 0.5, dur = 2.2) {
  const c = ac(); if (!c) return
  const now = c.currentTime + t
  const curve = new Float32Array(200)
  for (let i = 0; i < curve.length; i++) {
    const x = i / (curve.length - 1)
    curve[i] = (330 + 520 * Math.sin(Math.min(1, x * 1.15) * Math.PI * 0.62) - 120 * x) * (1 + 0.025 * Math.sin(i * 0.7) * x)
  }
  ;[1, 2.01].forEach((m, k) => {
    const o = c.createOscillator(), g = c.createGain()
    o.type = k ? 'triangle' : 'sine'; o.frequency.setValueCurveAtTime(curve.map((f) => f * m), now, dur)
    g.gain.setValueAtTime(0.0001, now); g.gain.exponentialRampToValueAtTime(v / (k + 1), now + 0.35); g.gain.setValueAtTime(v / (k + 1), now + dur - 0.5); g.gain.exponentialRampToValueAtTime(0.0001, now + dur)
    o.connect(g).connect(out(c)); o.start(now); o.stop(now + dur + 0.05)
  })
}
/** A cheering, clapping crowd. */
function crowd(sec: number, v = 0.4) {
  noise(0, sec, v, 1200, 0.4, 'bandpass', 2400)
  for (let i = 0; i < sec * 22; i++) noise(rand(0, sec), 0.03, rand(0.1, 0.3) * v * 1.6, rand(1500, 3200), 1.2)
}
/** Sci-fi laser zaps. */
function lasers(count: number, spanSec: number, v = 0.22) {
  for (let i = 0; i < count; i++) play([{ f: rand(2400, 4200), to: rand(160, 420), t: (i / count) * spanSec + rand(0, 0.08), d: 0.18, type: 'sawtooth', v }])
}
/** Shout through the browser's speech synthesis (only at Loud / INSANE). */
export function shout(text: string, pitch = 1.6, rate = 1.05) {
  if (volume !== 'loud' && volume !== 'insane') return
  try {
    const u = new SpeechSynthesisUtterance(text); u.pitch = pitch; u.rate = rate; u.volume = 1; u.lang = 'en-US'
    window.speechSynthesis.speak(u)
  } catch { /* speech unavailable */ }
}

/* ------------------------------------------------------------- party kit */
const PENTA = [523, 587, 659, 784, 880, 1047, 1175, 1319] // major pentatonic
/** Bubbly blips. */
function blip(count: number, spanSec: number, v = 0.22) {
  for (let i = 0; i < count; i++) play([{ f: rand(900, 2400), to: rand(1200, 3200), t: (i / count) * spanSec, d: 0.07, type: 'square', v }])
}
/** Rising sparkle glissando. */
function sparkle(t = 0, v = 0.28) {
  ;[0, 1, 2, 3, 4, 5].forEach((i) => bell(1568 * 1.26 ** i, t + i * 0.055, v, 0.7, false))
  play([{ f: 2000, to: 5200, t, d: 0.35, type: 'sine', v: v * 0.6 }])
}
/** Big tom-tom drum hit. */
function tom(t = 0, v = 0.9) {
  play([{ f: 140, to: 62, t, d: 0.35, type: 'sine', v }, { f: 90, to: 50, t, d: 0.4, type: 'triangle', v: v * 0.8 }])
  noise(t, 0.12, v * 0.7, 700, 0.8, 'lowpass', 120)
}
/** A bouncy plucked phrase. */
function pluckRun(t = 0, count = 8, step = 0.12, v = 0.3) {
  for (let i = 0; i < count; i++) {
    const f = PENTA[(i * 3 + (i >> 1)) % 6] / (i % 5 === 4 ? 2 : 1)
    play([{ f, t: t + i * step, d: 0.28, type: 'triangle', v }, { f: f * 2, t: t + i * step, d: 0.12, type: 'sawtooth', v: v * 0.35 }])
    noise(t + i * step, 0.02, v * 0.6, 3500, 2)
  }
}
/** Cute wolf bark: "wan!". */
function bark(t = 0, v = 0.45) {
  play([{ f: 520, to: 250, t, d: 0.13, type: 'sawtooth', v }, { f: 1040, to: 500, t, d: 0.1, type: 'square', v: v * 0.4 }])
  noise(t, 0.05, v * 0.6, 1500, 1)
}
/** Squeaky excitement (a pitch jump). */
function squeal(t = 0, v = 0.25) { play([{ f: 900, to: 2200, t, d: 0.22, type: 'sawtooth', v }, { f: 1800, to: 3300, t, d: 0.22, type: 'sine', v: v * 0.6 }]) }
/** Sweet looping party melody. */
function partyTune(sec: number, v = 0.22) {
  const mel = [1319, 1568, 1760, 1568, 1319, 1175, 1319, 1568, 2093, 1760, 1568, 1760, 1319, 1175, 1047, 1175]
  const step = 0.16
  for (let i = 0; i < sec / step; i++) {
    const f = mel[i % mel.length]
    play([{ f, t: i * step, d: step * 1.1, type: 'sine', v }, { f: f * 2, t: i * step, d: 0.05, type: 'triangle', v: v * 0.5 }])
    if (i % 4 === 0) play([{ f: [262, 349, 392, 330][(i >> 2) % 4], t: i * step, d: step * 3.5, type: 'triangle', v: v * 0.9 }])
  }
}

export const sfx = {
  click: () => play([{ f: 520, d: 0.05, type: 'triangle', v: 0.08 }]),
  tick: () => play([{ f: 1300, d: 0.03, type: 'square', v: 0.035 }]),
  thunk: () => play([{ f: 170, to: 70, d: 0.14, type: 'triangle', v: 0.22 }]),
  coin: () => play([{ f: 988, d: 0.07, type: 'square', v: 0.07 }, { f: 1319, t: 0.07, d: 0.22, type: 'square', v: 0.07 }]),
  buy: () => play([...notes([784, 988, 1175], 0.07, { type: 'triangle', d: 0.14 }), { f: 1568, t: 0.24, d: 0.3, type: 'triangle' }]),
  equip: () => play([{ f: 440, to: 880, d: 0.12, type: 'triangle' }]),
  claim: () => play(notes([523, 659, 784], 0.08, { type: 'triangle', d: 0.18 })),
  win: () => play(notes([523, 659, 784, 1047], 0.09, { type: 'triangle', d: 0.2 })),
  jackpot: () => { ching(0, 0.6); coinShower(30, 2); fanfare(0.1) },
  chest: () => play([{ f: 120, to: 90, d: 0.35, type: 'sawtooth', v: 0.1 }, ...notes([392, 523, 659, 784, 1047], 0.08, { t: 0.3, type: 'triangle', d: 0.25 } as Partial<Tone>)]),
  levelUp: () => play(notes([392, 494, 587, 784, 988], 0.1, { type: 'triangle', d: 0.3 })),
  oops: () => play([{ f: 330, to: 150, d: 0.35, type: 'sawtooth', v: 0.08 }]),
  pet: () => play([{ f: 660, to: 880, d: 0.12, type: 'sine' }, { f: 880, to: 1100, t: 0.1, d: 0.14, type: 'sine' }]),

  /** Reel whirr + machine-gun ticking for `ms`. Returns a stop function. */
  whir(ms: number) {
    const c = ac(); if (!c) return () => {}
    const now = c.currentTime
    const o = c.createOscillator(), lp = c.createBiquadFilter(), g = c.createGain()
    o.type = 'sawtooth'; o.frequency.setValueAtTime(70, now); o.frequency.linearRampToValueAtTime(240, now + ms / 1000 * 0.6); o.frequency.linearRampToValueAtTime(95, now + ms / 1000)
    lp.type = 'lowpass'; lp.frequency.value = 800
    g.gain.setValueAtTime(0.0001, now); g.gain.exponentialRampToValueAtTime(0.4, now + 0.15); g.gain.setValueAtTime(0.4, now + ms / 1000 - 0.4); g.gain.exponentialRampToValueAtTime(0.0001, now + ms / 1000)
    o.connect(lp).connect(g).connect(out(c)); o.start(now); o.stop(now + ms / 1000 + 0.05)
    riser(Math.min(ms / 1000, 2.8), 0.16)
    const iv = window.setInterval(() => { noise(0, 0.025, 0.45, 1800, 3); play([{ f: 1500, d: 0.03, type: 'square', v: 0.12 }]) }, 55)
    const to = window.setTimeout(() => clearInterval(iv), ms)
    return () => { clearInterval(iv); clearTimeout(to) }
  },
  /** A reel slamming into place: huge clunk, alarm bell, spark. */
  reelStop: () => { play([{ f: 220, to: 45, d: 0.28, type: 'triangle', v: 0.8 }, { f: 90, to: 40, d: 0.3, type: 'sine', v: 0.8 }]); noise(0, 0.1, 0.7, 900, 1); bell(1568, 0.02, 0.4, 0.7); bell(2093, 0.1, 0.3, 0.6) },
  /** Lever / wheel launch: crunchy slam + rising cha-ching. */
  leverPull: () => { play([{ f: 150, to: 50, d: 0.35, type: 'sawtooth', v: 0.5 }]); noise(0.05, 0.15, 0.6, 600, 1); ching(0.25, 0.45); boom(0, 0.35) },
  /** Roulette ball on a pin: sharp woody CRACK. */
  rtick: () => { noise(0, 0.035, 0.8, 2400, 2); play([{ f: 1000, to: 600, d: 0.05, type: 'square', v: 0.25 }, { f: 160, to: 90, d: 0.05, type: 'triangle', v: 0.3 }]) },
  ching: () => { ching(0, 0.7); ching(0.16, 0.7) },

  /** 1 = nice win, 2 = big win, 3 = jackpot (full sensory assault). */
  bigWin(level: number) {
    if (level <= 1) {
      for (let i = 0; i < 5; i++) ching(i * 0.14, 0.7)
      horn(0.05, 0.5, 0.35, 523); coinShower(40, 1.8); crash(0.05, 0.4); fanfare(0.1, 0.24); lasers(5, 0.8)
      blip(14, 1.2); sparkle(0.1); bark(0.3); bark(0.5); squeal(0.2)
      window.setTimeout(() => shout('Yay!', 1.9, 1.1), 250)
    } else if (level === 2) {
      riser(0.5, 0.45); snareRoll(0.5, 0.5)
      boom(0.5, 0.9); horn(0.5, 1.0, 0.45); horn(1.7, 0.9, 0.45, 587); howl(0.6, 0.45, 1.8)
      siren(2.6, 0.28); fanfare(0.5, 0.38); crash(0.5, 0.6); dance(3.6, 0.45); crowd(3.2, 0.35); lasers(14, 3, 0.2)
      for (let i = 0; i < 10; i++) ching(0.5 + i * 0.22, 0.75)
      coinShower(110, 3.6); arcade(3.2, 0.2)
      blip(40, 3.4); sparkle(0.4); sparkle(1.2); sparkle(2.4); tom(0.5); tom(0.75); tom(1.0); pluckRun(1.1, 12, 0.12); partyTune(3.4, 0.18)
      for (let i = 0; i < 7; i++) { bark(1 + i * 0.3, 0.5); squeal(1.05 + i * 0.3, 0.2) }
      window.setTimeout(() => shout('Awesome!', 1.9, 1.1), 500); window.setTimeout(() => shout('Big win!', 1.5, 1.05), 2200)
    } else {
      riser(1.1, 0.6); snareRoll(1.1, 0.65)
      boom(1.1, 1.0); boom(1.9, 0.95); boom(2.7, 0.95); boom(4.2, 0.9)
      horn(1.1, 1.3, 0.55); horn(2.4, 1.3, 0.55, 523); horn(3.7, 1.5, 0.55, 622); horn(5.4, 1.6, 0.55, 698)
      howl(1.2, 0.6, 2.4); howl(4.4, 0.6, 2.6)
      siren(7, 0.34, 600, 1800); crash(1.1, 0.75); crash(2.8, 0.7); crash(5.2, 0.7)
      fanfare(1.1, 0.46); fanfare(2.6, 0.46); fanfare(4.1, 0.46); fanfare(5.6, 0.46)
      dance(9, 0.55, 150); crowd(9, 0.5); lasers(40, 8, 0.24)
      for (let i = 0; i < 36; i++) ching(1.1 + i * 0.2, 0.8)
      coinShower(300, 9); arcade(8, 0.28)
      play([{ f: 60, to: 28, t: 1.1, d: 0.9, type: 'sine', v: 1.6 }, { f: 60, to: 28, t: 2.7, d: 0.9, type: 'sine', v: 1.6 }, { f: 60, to: 28, t: 4.2, d: 0.9, type: 'sine', v: 1.6 }])
      blip(90, 8.5); partyTune(9.5, 0.2); pluckRun(1.2, 20, 0.11); pluckRun(4.6, 20, 0.1)
      for (let i = 0; i < 6; i++) { tom(1.0 + i * 0.12, 0.9); sparkle(1.1 + i * 0.7, 0.3) }
      for (let i = 0; i < 24; i++) { tom(3.0 + i * 0.25, 0.7); bark(1.2 + i * 0.33, 0.5); squeal(1.3 + i * 0.4, 0.22) }
      window.setTimeout(() => shout('JACKPOT!', 1.9, 0.95), 900)
      window.setTimeout(() => shout('Yaaay! Yaaay!', 2, 1.15), 2800)
      window.setTimeout(() => shout('Mega jackpot! Wooo!', 1.7, 1.1), 4800)
      window.setTimeout(() => shout('Amazing!', 2, 1.1), 6800)
    }
  },
  /* mini-game sounds */
  menuSelect: () => { play([{ f: 880, to: 1320, d: 0.09, type: 'square', v: 0.12 }]); bell(2093, 0.05, 0.18, 0.5, false) },
  menuHover: () => play([{ f: 1200, d: 0.03, type: 'triangle', v: 0.06 }]),
  pegTick: (i = 0) => { play([{ f: 900 + (i % 6) * 120, to: 600, d: 0.06, type: 'triangle', v: 0.28 }]); noise(0, 0.02, 0.3, 4000, 2) },
  plinkoLand: () => { play([{ f: 180, to: 60, d: 0.3, type: 'triangle', v: 0.8 }]); bell(1568, 0.02, 0.35, 0.8); bell(2093, 0.1, 0.3, 0.8) },
  boing: () => play([{ f: 300, to: 900, d: 0.18, type: 'sine', v: 0.35 }, { f: 500, to: 1400, t: 0.04, d: 0.16, type: 'triangle', v: 0.2 }]),
  carHorn: () => play([{ f: 340, d: 0.4, type: 'square', v: 0.35 }, { f: 430, d: 0.4, type: 'square', v: 0.3 }]),
  crash: () => { boom(0, 0.8); noise(0, 0.4, 0.7, 2500, 0.6); play([{ f: 400, to: 60, d: 0.5, type: 'sawtooth', v: 0.4 }]); squeal(0.05, 0.3) },
  sparkle: () => sparkle(0, 0.3),
  bark: () => { bark(0, 0.5); bark(0.2, 0.5) },
  yay: () => { blip(10, 0.7, 0.2); sparkle(0.1, 0.3); bark(0.15, 0.4) },
  megaOn: () => { ching(0, 0.6); horn(0.05, 0.4, 0.35, 523); lasers(6, 0.5); howl(0.15, 0.3, 1.0); sparkle(0.2, 0.3); bark(0.3); bark(0.5) },
  megaOff: () => play([{ f: 700, to: 150, d: 0.3, type: 'sawtooth', v: 0.15 }]),
}

/** Schedule decelerating wheel ticks that match an ease-out spin. Returns a cancel function. */
export function wheelTicks(durationMs: number, count: number): () => void {
  const timers: number[] = []
  riser(durationMs / 1000 * 0.55, 0.22)
  for (let k = 1; k <= count; k++) {
    const t = (1 - Math.pow(1 - k / count, 1 / 3)) * durationMs
    timers.push(window.setTimeout(k > count - 5 ? () => { sfx.rtick(); bell(1568, 0, 0.3, 0.5); if (k === count) { ching(0.05, 0.6); crash(0, 0.3) } } : sfx.rtick, t))
  }
  return () => timers.forEach(clearTimeout)
}
