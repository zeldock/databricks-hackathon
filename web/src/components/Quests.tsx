import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Check, Flame, Gift, Snowflake } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge, Btn, Card, CardHead, Modal, Progress, notifyChange, useToast } from './ui'
import { api } from '../api'
import type { Json } from '../api'
import { sfx } from '../sound'

type Prize = { tokens: number; prize?: { name: string } | null; freeze?: boolean; weekly?: boolean }

function ChestModal({ prize, onClose }: { prize: Prize | null; onClose: () => void }) {
  return (
    <Modal open={!!prize} onClose={onClose}>
      {prize && (
        <div style={{ textAlign: 'center' }}>
          <motion.div initial={{ rotate: 0, scale: 0.6 }} animate={{ rotate: [0, -12, 12, -10, 10, 0], scale: [0.6, 1.3, 1.3, 1.5, 1.2, 1.3] }} transition={{ duration: 0.9 }} style={{ fontSize: 84 }}>{prize.weekly ? '🏆' : '🎁'}</motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9 }}>
            <h3 style={{ fontSize: 26 }}>{prize.weekly ? 'Weekly chest!' : 'Daily chest!'}</h3>
            <div className="num" style={{ fontSize: 46, color: 'var(--glow)' }}>+{prize.tokens} 🪙</div>
            {prize.prize && <p style={{ color: 'var(--warning)' }}>✨ Bonus item: <b>{prize.prize.name}</b></p>}
            {prize.freeze && <p style={{ color: 'var(--info)' }}>❄️ Bonus Streak Freeze!</p>}
            <Btn kind="primary" onClick={onClose} style={{ marginTop: 14 }}>Awesome</Btn>
          </motion.div>
        </div>)}
    </Modal>
  )
}

export function QuestsCard({ pet, compact }: { pet: Json; compact?: boolean }) {
  const toast = useToast()
  const [prize, setPrize] = useState<Prize | null>(null)
  const q = pet.quests
  const run = async (fn: () => Promise<Json>, after?: (r: Json) => void) => {
    try { const r = await fn(); after?.(r); notifyChange() } catch (e) { sfx.oops(); toast((e as Error).message, true) }
  }
  const claimed = q.items.filter((i: { claimed: boolean }) => i.claimed).length
  return (
    <Card delay={0.1}>
      <CardHead title="Daily quests" sub={`${claimed} of ${q.items.length} claimed · resets at midnight`}>
        <Badge tone={q.all_claimed ? '' : 'mute'}>{q.chest_opened ? 'Chest opened ✓' : q.all_claimed ? 'Chest ready!' : 'Chest locked'}</Badge>
      </CardHead>
      <div className="stack" style={{ gap: 10 }}>
        {q.items.map((i: { id: string; label: string; progress: number; target: number; reward: number; done: boolean; claimed: boolean }) => (
          <motion.div key={i.id} layout style={{ padding: '12px 14px', borderRadius: 14, background: i.done && !i.claimed ? 'var(--deep)' : 'var(--bg-base)', border: `1px solid ${i.done && !i.claimed ? 'var(--brand)' : 'var(--border-subtle)'}`, boxShadow: i.done && !i.claimed ? '0 0 22px #2db32d44' : 'none' }}>
            <div className="row spread" style={{ gap: 10 }}>
              <div className="grow">
                <div style={{ fontWeight: 600, textDecoration: i.claimed ? 'line-through' : 'none', opacity: i.claimed ? 0.5 : 1 }}>{i.label}</div>
                {!compact && <div style={{ marginTop: 8 }}><Progress value={i.progress / i.target} /></div>}
                <div className="small faint" style={{ marginTop: 4 }}>{Math.floor(i.progress)} / {i.target}</div>
              </div>
              {i.claimed ? <Badge><Check size={12} /> Done</Badge> : (
                <Btn kind={i.done ? 'primary sm' : 'sm'} disabled={!i.done} onClick={() => run(() => api.post('/quests/claim', { id: i.id }), () => sfx.claim())}>+{i.reward} 🪙{i.done ? ' Claim' : ''}</Btn>)}
            </div>
          </motion.div>))}
      </div>
      <div className="divider" />
      <div className="row spread" style={{ gap: 12 }}>
        <div className="row"><Gift color="var(--glow)" /><div><b>Daily chest</b><div className="small muted">Claim all 3 quests to unlock</div></div></div>
        <Btn kind={q.all_claimed && !q.chest_opened ? 'primary' : ''} disabled={!q.all_claimed || q.chest_opened} onClick={() => run(() => api.post('/quests/chest'), (r) => { sfx.chest(); setPrize(r) })}>{q.chest_opened ? 'Opened ✓' : 'Open chest'}</Btn>
      </div>
      <div className="row spread" style={{ gap: 12, marginTop: 14 }}>
        <div><b>Weekly chest</b><div className="row" style={{ gap: 6, marginTop: 6 }}>
          {Array.from({ length: q.weekly.goal }).map((_, i) => <motion.div key={i} animate={{ scale: i < q.weekly.days ? [1, 1.25, 1] : 1 }} style={{ width: 22, height: 22, borderRadius: '50%', background: i < q.weekly.days ? 'var(--glow)' : 'var(--bg-overlay)', boxShadow: i < q.weekly.days ? '0 0 12px var(--glow)' : 'none' }} />)}
          <span className="small muted">{q.weekly.days}/{q.weekly.goal} chest days this week</span></div></div>
        <Btn kind={q.weekly.claimable ? 'primary' : ''} disabled={!q.weekly.claimable} onClick={() => run(() => api.post('/quests/weekly'), (r) => { sfx.jackpot(); setPrize({ ...r, weekly: true }) })}>{q.weekly.opened ? 'Opened ✓' : 'Open weekly'}</Btn>
      </div>
      <ChestModal prize={prize} onClose={() => setPrize(null)} />
    </Card>
  )
}

/** Banner: streak in danger (live countdown) or saved by a Streak Freeze. */
export function StreakAlert({ pet }: { pet: Json }) {
  const risk = pet.streak_risk
  const [now, setNow] = useState(Date.now())
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 30000); return () => clearInterval(t) }, [])
  const ms = Math.max(0, new Date(risk.ends_at).getTime() - now)
  const h = Math.floor(ms / 3600000), m = Math.floor((ms % 3600000) / 60000)
  if (pet.freeze_notice) return (
    <Card style={{ marginBottom: 20, borderColor: '#4cc9f088' }}><div className="row"><Snowflake color="var(--info)" /><b>A Streak Freeze saved your {pet.freeze_notice.streak}-day streak!</b><span className="muted">You have {pet.freezes} left.</span></div></Card>)
  if (!risk.at_risk || risk.streak < 2) return null
  const urgent = h < 4
  const col = urgent ? 'var(--danger)' : 'var(--warning)'
  return (
    <Card style={{ marginBottom: 20, borderColor: `${col}88`, boxShadow: `0 0 36px ${urgent ? '#ff5c6c33' : '#ffb02033'}` }}>
      <div className="row spread" style={{ gap: 14 }}>
        <div className="row" style={{ gap: 12 }}>
          <Flame size={28} color={col} className={urgent ? 'pulse' : ''} />
          <div><b style={{ fontSize: 16 }}>Your {risk.streak}-day streak ends in <span style={{ color: col }}>{h}h {String(m).padStart(2, '0')}m</span></b>
            <div className="small muted">Study just 5 minutes to keep it.{risk.freezes > 0 ? ` ❄️ You hold ${risk.freezes} Streak Freeze${risk.freezes > 1 ? 's' : ''} as a backup.` : ' Buy a Streak Freeze in the shop for a safety net.'}</div></div>
        </div>
        <Link to="/log" className="btn primary">Start studying</Link>
      </div>
    </Card>)
}
