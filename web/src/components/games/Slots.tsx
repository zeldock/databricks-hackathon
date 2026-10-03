import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../api'
import type { Json } from '../../api'
import { Btn, notifyChange as notifyPet, useToast } from '../ui'
import { sfx } from '../../sound'
import { isMega } from '../../mega'
import { Celebration, Marquee } from '../Celebration'

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

export default function SlotGame({ sessionId, pet, onDone }: { sessionId: string; pet: Json; onDone: (r: Json) => void }) {
  const toast = useToast()
  const symbols: string[] = pet.slot_symbols.map((s: { symbol: string }) => s.symbol)
  const [reels, setReels] = useState<string[]>(['🐺', '🌙', '⭐'])
  const [spinning, setSpinning] = useState(false)
  const [result, setResult] = useState<Json>(null)
  const [landed, setLanded] = useState(0)
  const [burst, setBurst] = useState(0)
  const [tier, setTier] = useState(0)
  const pull = async () => {
    if (spinning) return
    try {
      const r = await api.post('/games/slot', { session_id: sessionId, mega: isMega() })
      setReels(r.reels); setResult(r); setSpinning(true); notifyPet(); sfx.leverPull(); sfx.whir(3000)
    } catch (e) { toast((e as Error).message, true) }
  }
  useEffect(() => {
    if (landed !== 3 || !result) return
    const t = result.kind === 'jackpot' ? (result.payout >= 60 ? 3 : 2) : result.kind === 'pair' ? 1 : 0
    setTier(t)
    if (t) { sfx.bigWin(t); setBurst((b) => b + 1) } else sfx.oops()
  }, [landed, result])
  const done = landed === 3
  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <Celebration level={tier} burst={burst} label={result ? `+${result.payout} 🪙` : ''} />
      <div className="caps">BONUS GAME · SLOTS</div>
      <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '4px 0 18px' }}>Wolf <span style={{ color: 'var(--glow)' }}>Slots</span></h2>
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 22 }}>
        <div className={`machine ${tier ? 'winning' : ''}`} style={{ position: 'relative', display: 'flex', gap: 12, padding: '26px 18px', borderRadius: 28, background: 'linear-gradient(145deg, #1b261c, #0a0f0b)', border: '2px solid var(--brand)', boxShadow: '0 0 50px #2db32d55, inset 0 0 30px #000' }}>
          <Marquee hot={spinning || tier > 0} />
          {tier >= 2 && <div className="flames">{Array.from({ length: 22 }, (_, i) => <span key={i} style={{ left: `${(i * 4.7) % 100}%`, animationDelay: `${(i % 7) * 0.13}s` }}>🔥</span>)}</div>}
          {reels.map((r, i) => <Reel key={i} target={r} symbols={symbols} spinning={spinning} delay={i} onDone={() => { sfx.reelStop(); setLanded((n) => n + 1) }} />)}
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
            <Btn kind="primary" onClick={() => onDone(result)} style={{ marginTop: 12 }}>Back to the games →</Btn>
          </motion.div>
        )}
      </div>
      <div className="small faint">🐺 ×3 = 60 · 💎 ×3 = 75 · ⭐ ×3 = 40 · any pair pays too</div>
    </div>
  )
}

