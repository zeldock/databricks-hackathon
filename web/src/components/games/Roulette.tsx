import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../api'
import type { Json } from '../../api'
import { Btn, notifyChange as notifyPet, useToast } from '../ui'
import { sfx, wheelTicks } from '../../sound'
import { isMega } from '../../mega'
import { Celebration } from '../Celebration'

/* ---------------------------------------------------------- roulette */
const N = 16
const polar = (a: number, r: number) => [160 + r * Math.cos(((a - 90) * Math.PI) / 180), 160 + r * Math.sin(((a - 90) * Math.PI) / 180)]

export default function RouletteGame({ sessionId, pet, onDone }: { sessionId: string; pet: Json; onDone: (r: Json) => void }) {
  const toast = useToast()
  const colors: Record<string, string> = Object.fromEntries(pet.roulette.map((r: { id: string; color: string }) => [r.id, r.color]))
  const labels: Record<string, string> = Object.fromEntries(pet.roulette.map((r: { id: string; label: string }) => [r.id, r.label]))
  const layout: string[] = pet.roulette_layout
  const [rot, setRot] = useState(0)
  const [result, setResult] = useState<Json>(null)
  const [spinning, setSpinning] = useState(false)
  const [shown, setShown] = useState(false)
  const [burst, setBurst] = useState(0)
  const [tier, setTier] = useState(0)
  const spin = async () => {
    if (spinning) return
    try {
      const r = await api.post('/games/roulette', { session_id: sessionId, mega: isMega() })
      setResult(r); setSpinning(true); notifyPet()
      setRot(360 * 6 - (r.segment * (360 / N) + 360 / N / 2))
      sfx.leverPull(); wheelTicks(5500, 6 * N + r.segment + 1)
    } catch (e) { toast((e as Error).message, true) }
  }
  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <Celebration level={tier} burst={burst} label={result?.label} />
      <div className="caps">BONUS GAME · ROULETTE</div>
      <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '4px 0 10px' }}>Lucky <span style={{ color: 'var(--glow)' }}>Roulette</span></h2>
      <div style={{ position: 'relative', width: 320, margin: '0 auto' }} className={`wheel-wrap ${spinning || tier ? 'hot' : ''}`}>
        <div style={{ position: 'absolute', left: '50%', top: -8, transform: 'translateX(-50%)', zIndex: 3, width: 0, height: 0, borderLeft: '14px solid transparent', borderRight: '14px solid transparent', borderTop: '28px solid #ffe27a', filter: 'drop-shadow(0 0 8px #ffe27a)' }} />
        <svg viewBox="0 0 320 320" width="320" height="320" style={{ filter: 'drop-shadow(0 0 30px #2db32d66)' }}>
          <motion.g className="pv" animate={{ rotate: rot }} transition={{ duration: spinning ? 5.5 : 0, ease: [0.12, 0.7, 0.1, 1] }} style={{ originX: '160px', originY: '160px' }}
            onAnimationComplete={() => { if (spinning) { setShown(true); setSpinning(false); if (result) {
              const t = result.prize || result.amount >= 100 ? 3 : result.amount >= 50 ? 2 : result.amount >= 25 ? 1 : 0
              setTier(t); if (t) { sfx.bigWin(t); setBurst((b) => b + 1) } else sfx.ching()
            } } }}>
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
            <Btn kind="primary" onClick={() => onDone(result)} style={{ marginTop: 12 }}>Back to the games →</Btn>
          </motion.div>
        )}
      </div>
    </div>
  )
}

