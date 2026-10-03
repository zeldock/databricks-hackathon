import { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { api } from '../../api'
import type { Json } from '../../api'
import { Btn, notifyChange as notifyPet, useToast } from '../ui'
import { sfx } from '../../sound'
import { isMega } from '../../mega'
import { Celebration } from '../Celebration'
import Wolf from '../Wolf'

const LANE_H = 58
const VEHICLES = ['🚌', '🚕', '🛵', '🚐', '🚚', '🏎️', '🛺', '🚓']
const LANES = 10

type Run = { pos: number; cash: number; table: number[]; mega: boolean }

/** Crossy Road: hop lane by lane; a hidden car (decided by the server) can end the run. Cash out any time. */
export default function CrossyGame({ sessionId, pet, onDone }: { sessionId: string; pet: Json; onDone: (r: Json) => void }) {
  const toast = useToast()
  const [run, setRun] = useState<Run | null>(null)
  const [view, setView] = useState(0) // lane the camera/wolf is on (can run ahead of `run.pos` during a crash)
  const [status, setStatus] = useState<'loading' | 'running' | 'crashed' | 'cashed'>('loading')
  const [payout, setPayout] = useState(0)
  const [busy, setBusy] = useState(false)
  const [hops, setHops] = useState(0)
  const [tier, setTier] = useState(0)
  const [burst, setBurst] = useState(0)
  const started = useRef(false)

  const cars = useMemo(() => Array.from({ length: LANES }, (_, i) => ({
    dir: i % 2 ? 1 : -1, kids: Array.from({ length: 2 + (i % 2) }, (_, k) => ({ e: VEHICLES[(i * 3 + k * 5) % VEHICLES.length], delay: -Math.random() * 6, dur: 3 + Math.random() * 3.5, top: k % 2 ? 6 : 14 })),
    tone: ['#3a2a44', '#2a3a4a', '#3a3040', '#2a4040'][i % 4],
  })), [])

  useEffect(() => {
    if (started.current) return
    started.current = true
    api.post('/games/crossy/start', { session_id: sessionId, mega: isMega() })
      .then((r) => { setRun({ pos: r.pos, cash: r.cash, table: r.cash_table, mega: r.mega }); setView(r.pos); setStatus('running'); notifyPet(); sfx.leverPull() })
      .catch((e) => toast(e.message, true))
  }, [sessionId, toast])

  const finish = (amount: number, crashed: boolean) => {
    setPayout(amount); setStatus(crashed ? 'crashed' : 'cashed')
    const t = crashed ? 0 : amount >= 92 ? 3 : amount >= 46 ? 2 : amount >= 15 ? 1 : 0
    setTier(t)
    if (crashed) sfx.crash(); else if (t) { sfx.bigWin(t); setBurst((b) => b + 1) } else sfx.ching()
    notifyPet()
  }
  const hop = async () => {
    if (busy || status !== 'running' || !run) return
    setBusy(true); sfx.boing(); setHops((h) => h + 1)
    try {
      const r = await api.post('/games/crossy/hop', { session_id: sessionId })
      if (r.crashed) {
        setView(r.pos + 1)
        setTimeout(() => { sfx.carHorn(); setTimeout(() => finish(r.payout, true), 650) }, 380)
      } else {
        setRun({ ...run, pos: r.pos, cash: r.done ? run.table[run.table.length - 1] : r.cash }); setView(r.pos); sfx.sparkle()
        if (r.done) setTimeout(() => finish(r.payout, false), 450)
      }
    } catch (e) { toast((e as Error).message, true) }
    setTimeout(() => setBusy(false), 420)
  }
  const cashOut = async () => {
    if (busy || status !== 'running' || !run || run.pos === 0) return
    setBusy(true)
    try { const r = await api.post('/games/crossy/cashout', { session_id: sessionId }); finish(r.payout, false) } catch (e) { toast((e as Error).message, true) }
    setBusy(false)
  }
  // Mega mode: auto-hop all the way for the show.
  useEffect(() => {
    if (status !== 'running' || !run?.mega) return
    const t = setTimeout(hop, 560)
    return () => clearTimeout(t)
  }) // eslint-disable-line react-hooks/exhaustive-deps

  const rows = Array.from({ length: LANES + 2 }, (_, i) => i) // 0 = start, 1..10 = lanes, 11 = goal
  const crashed = status === 'crashed'
  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <Celebration level={tier} burst={burst} label={status === 'cashed' ? `+${payout} 🪙` : ''} />
      <div className="caps">BONUS GAME · CROSSY ROAD</div>
      <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '4px 0 10px' }}>Crossy <span style={{ color: '#7ff0c8' }}>Wolf</span></h2>
      <div style={{ display: 'flex', gap: 16, justifyContent: 'center', alignItems: 'stretch' }}>
        <div style={{ position: 'relative', width: 300, height: LANE_H * 6, overflow: 'hidden', borderRadius: 22, border: '3px solid #7ff0c8', boxShadow: '0 0 36px #7ff0c855', background: '#13202a' }}>
          <div className="crossy-world" style={{ transform: `translateY(${view * LANE_H}px)` }}>
            {rows.map((i) => (
              <div key={i} className={`lane ${i === 0 ? 'start' : i === LANES + 1 ? 'goal' : 'road'}`} style={{ bottom: i * LANE_H, height: LANE_H, ...(i > 0 && i <= LANES ? { background: cars[i - 1].tone } : {}) }}>
                {i === 0 && <span className="lane-label">🐾 START 🐾</span>}
                {i === LANES + 1 && <span className="lane-label">🏁 FINISH 🏁</span>}
                {i > 0 && i <= LANES && <>
                  <span className="lane-dash" />
                  {cars[i - 1].kids.map((c, k) => <span key={k} className="car" style={{ top: c.top, animationDelay: `${c.delay}s`, animationDuration: `${c.dur}s`, animationName: cars[i - 1].dir > 0 ? 'driveR' : 'driveL' }}>{c.e}</span>)}
                  <span className="lane-val">{run?.table[i - 1] ?? ''}</span>
                </>}
              </div>))}
          </div>
          {/* wolf stays on the bottom row; the world scrolls under it */}
          <motion.div key={hops} className="crossy-wolf" animate={crashed ? { scaleY: 0.25, y: 18, rotate: 12 } : { y: [0, -26, 0] }} transition={{ duration: crashed ? 0.2 : 0.38, delay: crashed ? 0.5 : 0 }}>
            <Wolf mood={crashed ? 'sad' : 'ecstatic'} equipped={{ ...pet.equipped, scene: null }} size={64} crop="head" scene={false} animate={false} />
          </motion.div>
          <AnimatePresence>{crashed && <motion.span key="boom" className="crossy-boom" initial={{ scale: 0, opacity: 0 }} animate={{ scale: [0, 1.6, 1.2], opacity: 1 }}>💥</motion.span>}</AnimatePresence>
          {crashed && <motion.div className="crash-car" initial={{ x: -140 }} animate={{ x: 420 }} transition={{ duration: 0.55, ease: 'easeIn', delay: 0.15 }}>🚌</motion.div>}
        </div>
        <div style={{ width: 92, display: 'flex', flexDirection: 'column-reverse', gap: 3, justifyContent: 'flex-start' }}>
          {run?.table.map((v, i) => (
            <div key={i} className="small" style={{ padding: '2px 8px', borderRadius: 8, textAlign: 'right', fontWeight: 800, background: run.pos === i + 1 && status === 'running' ? '#7ff0c8' : i < run.pos ? '#2a4040' : 'transparent', color: run.pos === i + 1 && status === 'running' ? '#04210f' : i < run.pos ? '#7ff0c8' : 'var(--text-3)' }}>
              {i + 1} · {v}🪙</div>))}
        </div>
      </div>
      <div style={{ minHeight: 92, marginTop: 14 }}>
        {status === 'loading' && <div className="muted pulse">Getting ready… 🐾</div>}
        {status === 'running' && run && (
          <div className="row" style={{ justifyContent: 'center' }}>
            <Btn kind="primary" onClick={hop} disabled={busy || run.mega}>{run.mega ? 'MEGA auto-hop! ✨' : 'Hop! 🐾'}</Btn>
            <Btn onClick={cashOut} disabled={busy || run.pos === 0 || run.mega}>Cash out 🪙 {run.cash}</Btn>
          </div>)}
        {(status === 'cashed' || crashed) && (
          <motion.div initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <div className="num" style={{ fontSize: 30, color: crashed ? 'var(--text-2)' : '#ffe27a' }}>{crashed ? `Splat! 💥 +${payout} 🪙 consolation` : `${tier >= 2 ? '🎉 ' : ''}+${payout} 🪙`}</div>
            <Btn kind="primary" onClick={() => onDone({ amount: payout, label: crashed ? 'Crashed' : 'Cashed out' })} style={{ marginTop: 10 }}>Back to the games →</Btn>
          </motion.div>)}
        {status === 'running' && <p className="small faint" style={{ marginTop: 8 }}>Each lane pays more… but a car could be waiting. Cash out before it hits!</p>}
      </div>
    </div>
  )
}
