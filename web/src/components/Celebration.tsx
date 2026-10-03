import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import Wolf from './Wolf'
import { DancingCrew, StickerFloat } from './Crew'

/* ------------------------------------------------------ celebration */
const BANNERS = ['', 'NICE WIN!', 'BIG WIN!!', 'MEGA JACKPOT!!!']
const CONFETTI = ['#4cf04c', '#ffe27a', '#ff5c9a', '#4cc9f0', '#c9a3ff', '#ff8a3d', '#ffffff', '#ff5c6c']

/** Full-screen win celebration. level 1 = nice, 2 = big, 3 = jackpot. Re-fires whenever `burst` changes. */
export function Celebration({ level, burst, label }: { level: number; burst: number; label?: string }) {
  const [on, setOn] = useState(false)
  const fx = useMemo(() => {
    const L = level
    const pieces = Array.from({ length: [0, 120, 300, 600][L] ?? 0 }, (_, i) => ({
      i, left: Math.random() * 100, delay: Math.random() * (L >= 3 ? 3.2 : 1.4), dur: 2.4 + Math.random() * 2.6,
      size: 7 + Math.random() * 10, color: CONFETTI[i % CONFETTI.length], rot: Math.random() * 900, sway: (Math.random() - 0.5) * 260,
      coin: L >= 2 && i % 6 === 0, spark: L >= 2 && i % 9 === 1, bill: L >= 2 && (i % 11 === 2 || i % 17 === 3), billE: i % 17 === 3 ? '🤑' : '💵',
    }))
    const works = Array.from({ length: [0, 2, 6, 18][L] ?? 0 }, (_, i) => ({
      i, x: 12 + Math.random() * 76, y: 12 + Math.random() * 55, delay: 0.15 + Math.random() * (L >= 3 ? 4.5 : 2.2),
      color: CONFETTI[(i * 3) % CONFETTI.length], rays: Array.from({ length: 26 }, (_, r) => ({ a: (r / 26) * 360, d: 80 + Math.random() * 90 })),
    }))
    const fountain = Array.from({ length: [0, 0, 70, 160][L] ?? 0 }, (_, i) => ({ i, dx: (Math.random() - 0.5) * 95, peak: 35 + Math.random() * 55, delay: Math.random() * (L >= 3 ? 3.5 : 1.8), dur: 1.6 + Math.random() * 1.2 }))
    const blast = Array.from({ length: L >= 3 ? 36 : 0 }, (_, i) => ({ i, e: ['💰', '🎰', '🐺', '💎', '🔥', '🤑', '👑', '🍀'][i % 8], dx: Math.cos(i * 1.7) * (30 + Math.random() * 40), dy: Math.sin(i * 1.7) * (25 + Math.random() * 30), delay: Math.random() * 0.4 }))
    const balloons = Array.from({ length: [0, 0, 14, 34][L] ?? 0 }, (_, i) => ({ i, left: Math.random() * 100, size: 46 + Math.random() * 40, delay: Math.random() * 3, dur: 4.5 + Math.random() * 3.5, sway: (Math.random() - 0.5) * 160, e: ['🎈', '🎈', '🎉', '🪩'][i % 4] }))
    const streaks = Array.from({ length: [0, 0, 8, 20][L] ?? 0 }, (_, i) => ({ i, top: Math.random() * 70, left: Math.random() * 60, delay: Math.random() * (L >= 3 ? 8 : 3.5) }))
    const flares = Array.from({ length: [0, 10, 24, 56][L] ?? 0 }, (_, i) => ({ i, x: Math.random() * 100, y: Math.random() * 100, size: 26 + Math.random() * 70, delay: Math.random() * (L >= 3 ? 10 : 4) }))
    const bolts = (L >= 3 ? [1.3, 3.0, 4.9, 7.2] : L === 2 ? [1.2] : []).map((delay, i) => {
      let x = 8 + Math.random() * 84, y = 0, d = `M${x} 0`
      while (y < 100) { y += 7 + Math.random() * 9; x += (Math.random() - 0.5) * 16; d += ` L${x.toFixed(1)} ${Math.min(y, 100).toFixed(1)}` }
      return { i, d, delay }
    })
    return { pieces, works, fountain, blast, balloons, streaks, flares, bolts }
  }, [burst, level]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!burst || !level) return
    setOn(true)
    if (level >= 2) { document.body.classList.add('quake'); setTimeout(() => document.body.classList.remove('quake'), level >= 3 ? 5200 : 1600) }
    const t = setTimeout(() => { setOn(false); document.body.classList.remove('quake') }, level >= 3 ? 14000 : level === 2 ? 7500 : 4200)
    return () => { clearTimeout(t); document.body.classList.remove('quake') }
  }, [burst, level])
  if (!on) return null
  return createPortal(
    <div className="celebrate" key={burst} aria-hidden>
      {level >= 2 && <div className="neon-edge" />}
      {level >= 2 && <div className="party-glow" />}
      {level >= 3 && <div className="rainbow" />}
      {level >= 2 && <><div className="spot a" /><div className="spot b" /></>}
      {level >= 2 && <div className={`flash ${level >= 3 ? 'mega' : ''}`} />}
      {level >= 3 && <div className="rays" />}
      {level >= 2 && [0, 0.3, 0.6, 0.9].map((d) => <i key={d} className="ring" style={{ animationDelay: `${d}s` }} />)}
      {fx.streaks.map((m) => <i key={m.i} className="streak" style={{ top: `${m.top}%`, left: `${m.left}%`, animationDelay: `${m.delay}s` }} />)}
      {fx.balloons.map((b) => <span key={b.i} className="balloon" style={{ left: `${b.left}%`, fontSize: b.size, animationDelay: `${b.delay}s`, animationDuration: `${b.dur}s`, ['--sway' as string]: `${b.sway}px` }}>{b.e}</span>)}
      {fx.bolts.map((b) => (
        <svg key={b.i} className="bolt" viewBox="0 0 100 100" preserveAspectRatio="none" style={{ animationDelay: `${b.delay}s` }}><path d={b.d} /></svg>))}
      {level >= 2 && <StickerFloat count={level >= 3 ? 64 : 24} spanSec={level >= 3 ? 10 : 4} />}
      {level >= 3 && <>
        <div className="mascot left"><Wolf mood="ecstatic" equipped={{ hat: 'crown', eyewear: 'shades', fur: 'fur_golden' }} size={250} scene={false} animate={false} /></div>
        <div className="mascot right"><Wolf mood="ecstatic" equipped={{ hat: 'party', eyewear: 'square', fur: 'fur_emerald', neck: 'bandana_pink' }} size={250} scene={false} animate={false} /></div>
        <div className="mascot mid-l"><Wolf mood="ecstatic" equipped={{ hat: 'wizard', fur: 'fur_midnight', neck: 'chain' }} size={200} scene={false} animate={false} /></div>
        <div className="mascot mid-r"><Wolf mood="ecstatic" equipped={{ hat: 'halo', eyewear: 'glasses', fur: 'fur_snow', neck: 'bowtie_blue' }} size={200} scene={false} animate={false} /></div>
      </>}
      {level >= 3 && <div className="crew-row back"><DancingCrew wolves={11} size={96} seed={4} /></div>}
      <div className="crew-row front"><DancingCrew wolves={[0, 4, 9, 14][level]} size={[0, 92, 118, 138][level]} seed={1} /></div>
      {level >= 2 && <><div className="ticker top"><span>{`★ ${level >= 3 ? 'MEGA JACKPOT' : 'BIG WIN'} ★ CONGRATULATIONS ★ KA-CHING ★ WINNER WINNER ★ `.repeat(8)}</span></div><div className="ticker bottom"><span>{`★ CASH OUT ★ ${level >= 3 ? 'JACKPOT' : 'WINNER'} ★ 🪙🪙🪙 ★ AWESOME ★ WOOOO ★ `.repeat(8)}</span></div></>}
      {fx.flares.map((f) => <i key={f.i} className="flare" style={{ left: `${f.x}%`, top: `${f.y}%`, width: f.size, height: f.size, animationDelay: `${f.delay}s` }} />)}
      {fx.works.map((w) => (
        <div key={w.i} className="work" style={{ left: `${w.x}%`, top: `${w.y}%`, animationDelay: `${w.delay}s`, ['--c' as string]: w.color }}>
          <b />{w.rays.map((r, k) => <i key={k} style={{ ['--a' as string]: `${r.a}deg`, ['--d' as string]: `${r.d}px`, animationDelay: `${w.delay}s` }} />)}
        </div>))}
      {fx.pieces.map((p) => (
        <span key={p.i} className={`fall ${p.coin || p.spark || p.bill ? 'emo' : ''}`}
          style={{ left: `${p.left}%`, animationDelay: `${p.delay}s`, animationDuration: `${p.dur}s`, ['--sway' as string]: `${p.sway}px`, ['--rot' as string]: `${p.rot}deg`,
            ...(p.coin || p.spark || p.bill ? { fontSize: 22 + p.size } : { width: p.size, height: p.size * 1.7, background: p.color, borderRadius: 2 }) }}>
          {p.coin ? '🪙' : p.spark ? '✨' : p.bill ? p.billE : ''}
        </span>))}
      {fx.fountain.map((c) => <span key={c.i} className="spout" style={{ animationDelay: `${c.delay}s`, animationDuration: `${c.dur}s`, ['--dx' as string]: `${c.dx}vw`, ['--peak' as string]: `${c.peak}vh` }}>🪙</span>)}
      {fx.blast.map((e) => <span key={e.i} className="blast" style={{ animationDelay: `${e.delay}s`, ['--dx' as string]: `${e.dx}vw`, ['--dy' as string]: `${e.dy}vh` }}>{e.e}</span>)}
      <div className={`win-banner l${level}`}>{BANNERS[level]}{label && <small>{label}</small>}</div>
    </div>,
    document.body,
  )
}

/** Chaser lights around a machine; they strobe when `hot`. */
export function Marquee({ hot, count = 14 }: { hot: boolean; count?: number }) {
  return (
    <>
      {['top', 'bottom'].map((side) => (
        <div key={side} className={`marquee ${side} ${hot ? 'hot' : ''}`}>
          {Array.from({ length: count }, (_, i) => <i key={i} style={{ animationDelay: `${(i % 2) * 0.25}s` }} />)}
        </div>))}
    </>
  )
}

