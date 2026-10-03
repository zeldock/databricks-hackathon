import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Coins, PartyPopper, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { Json } from '../api'
import { Btn, Counter, notifyChange as notifyPet, useToast } from './ui'
import { sfx, wheelTicks } from '../sound'
import Wolf from './Wolf'

/* ---------------------------------------------------------------- bus */
type Open = { sessionId: string; parts?: { label: string; amount: number }[]; tokens?: number }
const bus = new EventTarget()
export const openRewards = (o: Open) => bus.dispatchEvent(new CustomEvent('open', { detail: o }))

/* ---------------------------------------------------------- confetti */
function Confetti({ burst }: { burst: number }) {
  const bits = useMemo(() => Array.from({ length: 36 }, (_, i) => ({ i, x: (Math.random() - 0.5) * 560, y: -120 - Math.random() * 260, r: Math.random() * 720, e: ['🪙', '⭐', '✨', '🟢', '🐾'][i % 5] })), [burst]) // eslint-disable-line
  if (!burst) return null
  return (
    <div style={{ position: 'absolute', left: '50%', top: '40%', pointerEvents: 'none', zIndex: 5 }}>
      {bits.map((b) => (
        <motion.span key={`${burst}-${b.i}`} style={{ position: 'absolute', fontSize: 22 }} initial={{ x: 0, y: 0, opacity: 1, scale: 0.4 }}
          animate={{ x: b.x, y: [0, b.y, b.y + 380], opacity: [1, 1, 0], rotate: b.r, scale: 1 }} transition={{ duration: 1.8, ease: 'easeOut' }}>{b.e}</motion.span>
      ))}
    </div>
  )
}

/* -------------------------------------------------------------- slot */
const H = 104
function Reel({ target, symbols, spinning, delay, onDone }: { target: string; symbols: string[]; spinning: boolean; delay: number; onDone?: () => void }) {
  const strip = useMemo(() => {
    const s = Array.from({ length: 26 }, (_, i) => symbols[(i * 5 + delay * 7) % symbols.length])
    s[24] = target
    return s
  }, [target, symbols, delay])
  return (
    <div style={{ height: H, width: 104, overflow: 'hidden', borderRadius: 18, background: 'linear-gradient(#0a0f0b, #162018 50%, #0a0f0b)', border: '2px solid var(--border-strong)', boxShadow: 'inset 0 0 22px #000' }}>
      <motion.div initial={{ y: -H * 3 }} animate={{ y: spinning ? -H * 24 : -H * 3 }} transition={spinning ? { duration: 2 + delay * 0.7, delay: 0.15, ease: [0.12, 0.8, 0.2, 1] } : { duration: 0 }} onAnimationComplete={() => spinning && onDone?.()}>
        {strip.map((s, i) => <div key={i} style={{ height: H, display: 'grid', placeItems: 'center', fontSize: 58 }}>{s}</div>)}
      </motion.div>
    </div>
  )
}

function SlotStage({ sessionId, pet, onDone }: { sessionId: string; pet: Json; onDone: (r: Json) => void }) {
  const toast = useToast()
  const symbols: string[] = pet.slot_symbols.map((s: { symbol: string }) => s.symbol)
  const [reels, setReels] = useState<string[]>(['🐺', '🌙', '⭐'])
  const [spinning, setSpinning] = useState(false)
  const [result, setResult] = useState<Json>(null)
  const [landed, setLanded] = useState(0)
  const [burst, setBurst] = useState(0)
  const pull = async () => {
    if (spinning) return
    try {
      const r = await api.post('/games/slot', { session_id: sessionId })
      setReels(r.reels); setResult(r); setSpinning(true); notifyPet(); sfx.click()
      const iv = window.setInterval(sfx.tick, 85); window.setTimeout(() => clearInterval(iv), 2900)
    } catch (e) { toast((e as Error).message, true) }
  }
  useEffect(() => { if (landed === 3 && result) { if (result.kind === 'jackpot') sfx.jackpot(); else if (result.kind === 'pair') sfx.win(); else sfx.oops(); if (result.kind !== 'none') setBurst((b) => b + 1) } }, [landed, result])
  const done = landed === 3
  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <Confetti burst={burst} />
      <div className="caps">Bonus round 1 of 2</div>
      <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '4px 0 18px' }}>Wolf <span style={{ color: 'var(--glow)' }}>Slots</span></h2>
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 22 }}>
        <div style={{ display: 'flex', gap: 12, padding: 18, borderRadius: 28, background: 'linear-gradient(145deg, #1b261c, #0a0f0b)', border: '2px solid var(--brand)', boxShadow: '0 0 50px #2db32d55, inset 0 0 30px #000' }}>
          {reels.map((r, i) => <Reel key={i} target={r} symbols={symbols} spinning={spinning} delay={i} onDone={() => { sfx.thunk(); setLanded((n) => n + 1) }} />)}
        </div>
        <motion.button aria-label="Pull the lever" onClick={pull} disabled={spinning} whileTap={{ scale: 0.95 }} style={{ background: 'none', border: 0, cursor: spinning ? 'default' : 'pointer', padding: 0 }}>
          <div style={{ width: 14, height: 120, borderRadius: 8, background: 'var(--border-strong)', position: 'relative' }}>
            <motion.div animate={{ y: spinning ? [0, 78, 0] : 0 }} transition={{ duration: 0.6 }} style={{ position: 'absolute', left: -13, top: -10, width: 40, height: 40, borderRadius: '50%', background: 'radial-gradient(circle at 35% 30%, #ff9aa6, #ff5c6c 60%, #a8242f)', boxShadow: '0 0 20px #ff5c6c88' }} />
          </div>
        </motion.button>
      </div>
      <div style={{ minHeight: 78, marginTop: 20 }}>
        {!result && <Btn kind="primary" onClick={pull}>Pull the lever!</Btn>}
        {result && !done && <div className="muted pulse">Spinning…</div>}
        {done && (
          <motion.div initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <div className="num" style={{ fontSize: 34, color: result.kind === 'none' ? 'var(--text-2)' : 'var(--glow)' }}>
              {result.kind === 'jackpot' ? '🎉 JACKPOT! ' : result.kind === 'pair' ? 'Nice pair! ' : 'Not this time. '}+{result.payout} 🪙
            </div>
            <Btn kind="primary" onClick={() => onDone(result)} style={{ marginTop: 12 }}>On to the roulette →</Btn>
          </motion.div>
        )}
      </div>
      <div className="small faint">🐺 ×3 = 60 · 💎 ×3 = 75 · ⭐ ×3 = 40 · any pair pays too</div>
    </div>
  )
}

/* ---------------------------------------------------------- roulette */
const N = 16
const polar = (a: number, r: number) => [160 + r * Math.cos(((a - 90) * Math.PI) / 180), 160 + r * Math.sin(((a - 90) * Math.PI) / 180)]

function RouletteStage({ sessionId, pet, onDone }: { sessionId: string; pet: Json; onDone: (r: Json) => void }) {
  const toast = useToast()
  const colors: Record<string, string> = Object.fromEntries(pet.roulette.map((r: { id: string; color: string }) => [r.id, r.color]))
  const labels: Record<string, string> = Object.fromEntries(pet.roulette.map((r: { id: string; label: string }) => [r.id, r.label]))
  const layout: string[] = pet.roulette_layout
  const [rot, setRot] = useState(0)
  const [result, setResult] = useState<Json>(null)
  const [spinning, setSpinning] = useState(false)
  const [shown, setShown] = useState(false)
  const [burst, setBurst] = useState(0)
  const spin = async () => {
    if (spinning) return
    try {
      const r = await api.post('/games/roulette', { session_id: sessionId })
      setResult(r); setSpinning(true); notifyPet()
      setRot(360 * 6 - (r.segment * (360 / N) + 360 / N / 2))
      sfx.click(); wheelTicks(5500, 6 * N + r.segment + 1)
    } catch (e) { toast((e as Error).message, true) }
  }
  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <Confetti burst={burst} />
      <div className="caps">Bonus round 2 of 2</div>
      <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '4px 0 10px' }}>Lucky <span style={{ color: 'var(--glow)' }}>Roulette</span></h2>
      <div style={{ position: 'relative', width: 320, margin: '0 auto' }}>
        <div style={{ position: 'absolute', left: '50%', top: -8, transform: 'translateX(-50%)', zIndex: 3, width: 0, height: 0, borderLeft: '14px solid transparent', borderRight: '14px solid transparent', borderTop: '28px solid #ffe27a', filter: 'drop-shadow(0 0 8px #ffe27a)' }} />
        <svg viewBox="0 0 320 320" width="320" height="320" style={{ filter: 'drop-shadow(0 0 30px #2db32d66)' }}>
          <motion.g className="pv" animate={{ rotate: rot }} transition={{ duration: spinning ? 5.5 : 0, ease: [0.12, 0.7, 0.1, 1] }} style={{ originX: '160px', originY: '160px' }}
            onAnimationComplete={() => { if (spinning) { setShown(true); setSpinning(false); if (result && (result.amount >= 25 || result.prize)) { setBurst((b) => b + 1); sfx.jackpot() } else sfx.win() } }}>
            {layout.map((id, i) => {
              const a0 = (360 / N) * i, a1 = a0 + 360 / N, [x0, y0] = polar(a0, 150), [x1, y1] = polar(a1, 150), [tx, ty] = polar(a0 + 360 / N / 2, 106)
              return (<g key={i}><path d={`M160 160 L${x0} ${y0} A150 150 0 0 1 ${x1} ${y1}Z`} fill={colors[id]} stroke="#060906" strokeWidth="2" />
                <text x={tx} y={ty} fill="#fff" fontSize={id === 'mystery' || id === 'double' ? 10 : 15} fontWeight="800" textAnchor="middle" dominantBaseline="middle" transform={`rotate(${a0 + 360 / N / 2} ${tx} ${ty})`}>{labels[id]}</text></g>)
            })}
            <circle cx="160" cy="160" r="150" fill="none" stroke="#2db32d" strokeWidth="5" />
          </motion.g>
          <circle cx="160" cy="160" r="30" fill="#0d130e" stroke="#4cf04c" strokeWidth="4" />
          <text x="160" y="162" textAnchor="middle" dominantBaseline="middle" fontSize="26">🐾</text>
        </svg>
      </div>
      <div style={{ minHeight: 100, marginTop: 16 }}>
        {!result && <Btn kind="primary" onClick={spin}>Spin the wheel!</Btn>}
        {result && !shown && <div className="muted pulse">Round and round…</div>}
        {shown && (
          <motion.div initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <div className="num" style={{ fontSize: 28, color: 'var(--glow)' }}>{result.label}</div>
            <Btn kind="primary" onClick={() => onDone(result)} style={{ marginTop: 12 }}>Collect</Btn>
          </motion.div>
        )}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------- flow */
export function RewardHost() {
  const [open, setOpen] = useState<Open | null>(null)
  const [pet, setPet] = useState<Json>(null)
  const [step, setStep] = useState<'summary' | 'slot' | 'roulette' | 'done'>('summary')
  const [wins, setWins] = useState({ slot: 0, roulette: 0, label: '' })
  const [loadErr, setLoadErr] = useState('')

  const start = useCallback(async (o: Open) => {
    setLoadErr(''); setWins({ slot: 0, roulette: 0, label: '' })
    try {
      const p = await api.get('/pet'); setPet(p)
      const t = p.tickets.find((x: { session_id: string }) => x.session_id === o.sessionId)
      setStep(o.parts ? 'summary' : t?.stage === 'roulette' ? 'roulette' : t ? 'slot' : 'done')
      setOpen(o)
    } catch (e) { setLoadErr((e as Error).message) }
  }, [])
  useEffect(() => {
    const h = (e: Event) => start((e as CustomEvent<Open>).detail)
    bus.addEventListener('open', h)
    return () => bus.removeEventListener('open', h)
  }, [start])

  const close = () => { setOpen(null); notifyPet() }
  const total = (open?.tokens ?? 0) + wins.slot + wins.roulette
  return (
    <AnimatePresence>
      {open && pet && (
        <motion.div className="modal-bg" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <motion.div className="modal" style={{ width: 'min(620px, 100%)', position: 'relative', overflow: 'hidden', maxHeight: '94vh', overflowY: 'auto' }}
            initial={{ scale: 0.85, y: 40, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} transition={{ type: 'spring', stiffness: 300, damping: 26 }}>
            <button className="btn ghost sm icon" style={{ position: 'absolute', right: 14, top: 14, zIndex: 6 }} onClick={close} aria-label="Close"><X size={18} /></button>
            {loadErr && <p style={{ color: 'var(--danger)' }}>{loadErr}</p>}
            {step === 'summary' && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Wolf mood="ecstatic" equipped={pet.equipped} size={190} /></div>
                <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '14px 0 4px' }}>Session <span style={{ color: 'var(--glow)' }}>complete!</span></h2>
                <p className="muted">{pet.name} is proud of you.</p>
                <div style={{ margin: '16px auto 0', maxWidth: 360, textAlign: 'left' }}>
                  {open.parts?.map((p, i) => (
                    <motion.div key={i} className="row spread" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.12 }} style={{ padding: '7px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span className="muted">{p.label}</span><b style={{ color: p.amount < 0 ? 'var(--warning)' : 'var(--glow)' }}>{p.amount > 0 ? '+' : ''}{p.amount} 🪙</b>
                    </motion.div>))}
                  <div className="row spread" style={{ padding: '12px 0 0' }}><b>Total</b><span className="num" style={{ fontSize: 26, color: 'var(--glow)' }}><Counter value={open.tokens ?? 0} /> 🪙</span></div>
                </div>
                <div className="row" style={{ justifyContent: 'center', marginTop: 20 }}>
                  <Btn onClick={close}>Play later</Btn><Btn kind="primary" icon={PartyPopper} onClick={() => setStep('slot')}>Spin the slots!</Btn>
                </div>
              </div>)}
            {step === 'slot' && <SlotStage sessionId={open.sessionId} pet={pet} onDone={(r) => { setWins((w) => ({ ...w, slot: r.payout })); setStep('roulette') }} />}
            {step === 'roulette' && <RouletteStage sessionId={open.sessionId} pet={pet} onDone={(r) => { setWins((w) => ({ ...w, roulette: r.amount, label: r.prize ? r.label : '' })); setStep('done') }} />}
            {step === 'done' && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Wolf mood="ecstatic" equipped={pet.equipped} size={190} /></div>
                <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '14px 0 4px' }}>All done, <span style={{ color: 'var(--glow)' }}>nice work!</span></h2>
                <div className="num" style={{ fontSize: 44, color: 'var(--glow)' }}><Coins size={34} style={{ verticalAlign: -4 }} /> +<Counter value={total} /></div>
                <p className="muted small">{open.tokens ?? 0} from studying · {wins.slot} from the slots · {wins.roulette} from the roulette{wins.label ? ` · ${wins.label}` : ''}</p>
                <div className="row" style={{ justifyContent: 'center', marginTop: 18 }}>
                  <Btn onClick={close}>Close</Btn><Link to="/den" className="btn primary" onClick={close}>Spend tokens in the Den</Link>
                </div>
              </div>)}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

