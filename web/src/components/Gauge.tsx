import { useEffect } from 'react'
import { animate, motion, useMotionValue, useTransform } from 'framer-motion'

const TIER = {
  on_track: { color: '#4cf04c', label: 'On track' },
  watch: { color: '#ffb020', label: 'Keep an eye on it' },
  at_risk: { color: '#ff5c6c', label: 'At risk' },
} as const

export const tierInfo = (t: string) => TIER[t as keyof typeof TIER] ?? TIER.on_track

/** Semi-circular risk dial: needle and arc spring toward the new probability. */
export default function Gauge({ probability, tier, size = 280 }: { probability: number; tier: string; size?: number }) {
  const p = useMotionValue(0)
  useEffect(() => {
    const c = animate(p, probability, { type: 'spring', stiffness: 70, damping: 16 })
    return () => c.stop()
  }, [probability, p])
  const r = 100, cx = 130, cy = 130, len = Math.PI * r
  const dash = useTransform(p, (v) => `${v * len} ${len}`)
  const angle = useTransform(p, (v) => -90 + v * 180)
  const text = useTransform(p, (v) => `${Math.round(v * 100)}%`)
  const { color, label } = tierInfo(tier)
  const arc = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`
  return (
    <div style={{ width: size, margin: '0 auto', textAlign: 'center' }}>
      <svg viewBox="0 0 260 160" width="100%">
        <defs>
          <linearGradient id="gtrack" x1="0" x2="1"><stop offset="0" stopColor="#4cf04c" /><stop offset=".5" stopColor="#ffb020" /><stop offset="1" stopColor="#ff5c6c" /></linearGradient>
          <filter id="gglow"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        <path d={arc} fill="none" stroke="#1f2d21" strokeWidth="16" strokeLinecap="round" />
        <path d={arc} fill="none" stroke="url(#gtrack)" strokeWidth="16" strokeLinecap="round" opacity=".18" />
        <motion.path d={arc} fill="none" stroke={color} strokeWidth="16" strokeLinecap="round" style={{ strokeDasharray: dash }} filter="url(#gglow)" />
        <motion.g className="pv" style={{ rotate: angle, originX: `${cx}px`, originY: `${cy}px` }}>
          <line x1={cx} y1={cy} x2={cx} y2={cy - r + 18} stroke="#eaf4ea" strokeWidth="3" strokeLinecap="round" />
        </motion.g>
        <circle cx={cx} cy={cy} r="9" fill="#060906" stroke={color} strokeWidth="3" />
      </svg>
      <motion.div className="num" style={{ fontSize: 54, color, marginTop: -26, textShadow: `0 0 30px ${color}88` }}>{text}</motion.div>
      <div className="caps" style={{ color }}>{label} · chance of a D or F</div>
    </div>
  )
}
