import { useEffect, useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../api'
import type { Json } from '../../api'
import { Btn, notifyChange as notifyPet, useToast } from '../ui'
import { sfx } from '../../sound'
import { isMega } from '../../mega'
import { Celebration } from '../Celebration'

const CX = 180, DX = 13, ROW = 28, Y0 = 62, ROWS = 12
const px = (r: number, k: number) => CX + (2 * k - r) * DX
const py = (r: number) => Y0 + r * ROW
const BIN_Y = py(ROWS - 1) + 26
const PER_ROW = 0.27

/** Plinko: the server decides the path; the ball follows it peg by peg. */
export default function PlinkoGame({ sessionId, pet, onDone }: { sessionId: string; pet: Json; onDone: (r: Json) => void }) {
  const toast = useToast()
  const payouts: number[] = pet.plinko.payouts
  const [result, setResult] = useState<Json>(null)
  const [dropping, setDropping] = useState(false)
  const [landed, setLanded] = useState(false)
  const [hit, setHit] = useState<number[]>([])
  const [tier, setTier] = useState(0)
  const [burst, setBurst] = useState(0)
  const timers = useRef<number[]>([])
  useEffect(() => () => timers.current.forEach(clearTimeout), [])

  // Keyframes for the ball along the decided path: above each peg, then deflected to the next row.
  const track = useMemo(() => {
    if (!result) return null
    const xs: number[] = [CX], ys: number[] = [18]
    let rights = 0
    for (let r = 0; r < ROWS; r++) {
      xs.push(px(r, rights)); ys.push(py(r) - 13)
      rights += result.path[r]
      xs.push(px(r + 1, rights)); ys.push(py(r) + 11)
    }
    xs.push(px(ROWS, rights)); ys.push(BIN_Y + 22)
    const n = xs.length
    return { xs, ys, times: xs.map((_, i) => i / (n - 1)), total: ROWS * PER_ROW + 0.5 }
  }, [result])

  const drop = async () => {
    if (dropping) return
    try {
      const r = await api.post('/games/plinko', { session_id: sessionId, mega: isMega() })
      setResult(r); setDropping(true); notifyPet(); sfx.leverPull()
      for (let i = 0; i < ROWS; i++) timers.current.push(window.setTimeout(() => { sfx.pegTick(i); setHit((h) => [...h, i]) }, (0.12 + (i + 0.55) * PER_ROW) * 1000))
    } catch (e) { toast((e as Error).message, true) }
  }
  const finish = () => {
    if (!result) return
    setLanded(true); sfx.plinkoLand()
    const t = result.amount >= 80 ? 3 : result.amount >= 30 ? 2 : result.amount >= 16 ? 1 : 0
    setTier(t)
    if (t) { sfx.bigWin(t); setBurst((b) => b + 1) } else sfx.ching()
  }
  const binColor = (v: number) => (v >= 80 ? '#ff5c9a' : v >= 30 ? '#ffb020' : v >= 16 ? '#b79bff' : '#2db3a0')

  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <Celebration level={tier} burst={burst} label={result ? `+${result.amount} 🪙` : ''} />
      <div className="caps">BONUS GAME · PLINKO</div>
      <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '4px 0 6px' }}>Wolf <span style={{ color: '#ff8fc7' }}>Plinko</span></h2>
      <svg viewBox="0 0 360 470" width="100%" style={{ maxWidth: 400, filter: 'drop-shadow(0 0 28px #ff8fc755)' }}>
        <defs>
          <linearGradient id="pk-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2a1630" /><stop offset="1" stopColor="#13202a" /></linearGradient>
          <radialGradient id="pk-ball" cx=".35" cy=".3"><stop offset="0" stopColor="#fff" /><stop offset=".45" stopColor="#ffc2dc" /><stop offset="1" stopColor="#ff5c9a" /></radialGradient>
        </defs>
        <rect x="6" y="6" width="348" height="458" rx="26" fill="url(#pk-bg)" stroke="#ff8fc7" strokeWidth="3" />
        {Array.from({ length: 18 }, (_, i) => <text key={i} x={20 + (i * 37) % 330} y={30 + ((i * 53) % 330)} fontSize="12" opacity=".35">{i % 3 ? '✨' : '⭐'}</text>)}
        {Array.from({ length: ROWS }, (_, r) => Array.from({ length: r + 1 }, (_, k) => (
          <circle key={`${r}-${k}`} cx={px(r, k)} cy={py(r)} r={hit.includes(r) && result && px(r, 0) <= 999 ? 4.6 : 4.6}
            fill={hit.includes(r) ? '#fff' : '#ffd1e6'} opacity={hit.includes(r) ? 1 : 0.85} />)))}
        {payouts.map((v, k) => (
          <g key={k}>
            <rect x={px(ROWS, k) - 11.5} y={BIN_Y} width="23" height="46" rx="8" fill={binColor(v)} opacity={landed && result?.slot === k ? 1 : 0.55} stroke={landed && result?.slot === k ? '#fff' : 'none'} strokeWidth="3" />
            <text x={px(ROWS, k)} y={BIN_Y + 28} textAnchor="middle" fontSize={v >= 100 ? 10 : 11} fontWeight="800" fill="#fff">{v}</text>
          </g>))}
        {track && (
          <motion.g initial={{ x: 0, y: 0 }}>
            <motion.g initial={{ x: track.xs[0], y: track.ys[0] }} animate={{ x: track.xs, y: track.ys }} transition={{ duration: track.total, times: track.times, ease: 'linear' }} onAnimationComplete={finish}>
              <circle r="9.5" fill="url(#pk-ball)" stroke="#fff" strokeWidth="1.5" />
              <circle cx="-3.2" cy="-1" r="1.6" fill="#3b2430" /><circle cx="3.2" cy="-1" r="1.6" fill="#3b2430" /><path d="M-2.4 3 Q0 5 2.4 3" stroke="#3b2430" strokeWidth="1.2" fill="none" strokeLinecap="round" />
            </motion.g>
          </motion.g>)}
        {!track && <g transform={`translate(${CX} 20)`}><circle r="9.5" fill="url(#pk-ball)" stroke="#fff" strokeWidth="1.5" /><circle cx="-3.2" cy="-1" r="1.6" fill="#3b2430" /><circle cx="3.2" cy="-1" r="1.6" fill="#3b2430" /></g>}
      </svg>
      <div style={{ minHeight: 84, marginTop: 6 }}>
        {!result && <Btn kind="primary" onClick={drop}>Drop the ball! 🎯</Btn>}
        {result && !landed && <div className="muted pulse">Bouncing… 🎀</div>}
        {landed && (
          <motion.div initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <div className="num" style={{ fontSize: 30, color: tier ? '#ffe27a' : 'var(--glow)' }}>{tier >= 2 ? '🎉 ' : ''}+{result.amount} 🪙</div>
            <Btn kind="primary" onClick={() => onDone(result)} style={{ marginTop: 10 }}>Back to the games →</Btn>
          </motion.div>)}
      </div>
    </div>
  )
}
