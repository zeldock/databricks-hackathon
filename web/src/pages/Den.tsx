import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Check, Coins, Gift, Heart, Pencil, Sparkles } from 'lucide-react'
import { Badge, Btn, Card, CardHead, Loading, PageHeader, Progress, notifyChange, useApi, useToast } from '../components/ui'
import Wolf from '../components/Wolf'
import type { Equipped, Mood } from '../components/Wolf'
import { openRewards } from '../components/Rewards'
import { api } from '../api'
import { QuestsCard, StreakAlert } from '../components/Quests'
import { sfx } from '../sound'

const RARITY: Record<string, string> = { common: 'mute', rare: 'info', epic: '', legendary: 'warning' }
const MOODS: { key: Mood; emoji: string }[] = [{ key: 'ecstatic', emoji: '🤩' }, { key: 'happy', emoji: '😊' }, { key: 'content', emoji: '🙂' }, { key: 'worried', emoji: '😟' }, { key: 'sad', emoji: '😢' }]
type Item = { id: string; slot: string; name: string; price: number; rarity: string; desc: string }

export function CheckinButton({ pet, onPat, big }: { pet: { checkin: { available: boolean; amount: number }; name: string }; onPat?: () => void; big?: boolean }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const claim = async () => {
    setBusy(true)
    try { const r = await api.post('/pet/checkin'); sfx.pet(); toast(`${pet.name} loved that! +${r.amount} 🪙`); onPat?.(); notifyChange() }
    catch (e) { toast((e as Error).message, true) }
    setBusy(false)
  }
  return (
    <Btn kind={pet.checkin.available ? 'primary' : ''} icon={Heart} busy={busy} disabled={!pet.checkin.available} onClick={claim} style={big ? { padding: '14px 26px', fontSize: 15 } : undefined}>
      {pet.checkin.available ? `Pet ${pet.name} · +${pet.checkin.amount} 🪙` : 'Already petted today ✓'}
    </Btn>
  )
}

export default function Den() {
  const { data: pet } = useApi('/pet')
  const toast = useToast()
  const [tab, setTab] = useState('hat')
  const [preview, setPreview] = useState<Item | null>(null)
  const [moodPreview, setMoodPreview] = useState<Mood | null>(null)
  const [pat, setPat] = useState(0)
  const [hearts, setHearts] = useState<number[]>([])
  const [editing, setEditing] = useState<string | null>(null)
  if (!pet) return <Loading />

  const items: Item[] = tab === 'upgrade' ? [...pet.consumables, ...pet.upgrades] : pet.catalog.filter((i: Item) => i.slot === tab)
  const worn: Equipped = { ...pet.equipped, ...(preview && preview.slot !== 'upgrade' ? { [preview.slot]: preview.id } : {}) }
  const mood: Mood = moodPreview ?? pet.mood.key
  const act = async (fn: () => Promise<unknown>, msg?: string) => { try { await fn(); if (msg) toast(msg); notifyChange() } catch (e) { toast((e as Error).message, true) } }
  const poke = () => { sfx.pet(); setPat((n) => n + 1); setHearts((h) => [...h.slice(-6), Date.now()]) }
  const lv = pet.level
  const tabs = [...pet.slots.map((s: string) => [s, pet.slot_labels[s]]), ['upgrade', 'Upgrades']]

  return (
    <>
      <PageHeader title="My" accent="wolf" sub="Study to keep your wolf happy, earn tokens, and spend them on accessories and upgrades.">
        <div className="card" style={{ padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 10, borderColor: '#ffb02055' }}>
          <Coins color="var(--warning)" /><span className="num" style={{ fontSize: 28, color: 'var(--warning)' }}>{pet.tokens}</span><span className="muted">tokens</span>
        </div>
      </PageHeader>

      <StreakAlert pet={pet} />
      {pet.tickets.length > 0 && (
        <Card style={{ marginBottom: 20, borderColor: '#4cf04c77', boxShadow: '0 0 40px #2db32d33' }}>
          <div className="row spread"><div className="row"><Gift color="var(--glow)" /><b>You have an unplayed bonus round!</b><span className="muted">Slots and roulette are waiting.</span></div>
            <Btn kind="primary" onClick={() => openRewards({ sessionId: pet.tickets[0].session_id })}>Play now</Btn></div>
        </Card>)}

      <div className="grid cols-1-2" style={{ alignItems: 'start' }}>
        <div className="stack">
          <Card delay={0.05} style={{ padding: 18 }}>
            <div style={{ position: 'relative', display: 'flex', justifyContent: 'center', cursor: 'pointer' }} onClick={poke}>
              <Wolf mood={mood} equipped={worn} size={380} pat={pat} />
              <AnimatePresence>
                {hearts.map((h) => <motion.span key={h} initial={{ opacity: 1, y: 0, x: (h % 80) - 40, scale: 0.5 }} animate={{ opacity: 0, y: -140, scale: 1.4 }} exit={{ opacity: 0 }} transition={{ duration: 1.3 }}
                  onAnimationComplete={() => setHearts((x) => x.filter((v) => v !== h))} style={{ position: 'absolute', top: '24%', left: '50%', fontSize: 30, pointerEvents: 'none' }}>💚</motion.span>)}
              </AnimatePresence>
              {preview && <div style={{ position: 'absolute', top: 12, left: 12 }}><Badge tone="info">Previewing {preview.name}</Badge></div>}
            </div>
            <div className="row spread" style={{ marginTop: 16 }}>
              {editing === null ? (
                <div className="row"><h2 style={{ fontSize: 26, letterSpacing: -0.6 }}>{pet.name}</h2><Btn kind="ghost sm icon" aria-label="Rename" onClick={() => setEditing(pet.name)}><Pencil size={15} /></Btn></div>
              ) : (
                <div className="row"><input className="input" style={{ width: 170 }} autoFocus maxLength={20} value={editing} onChange={(e) => setEditing(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && act(async () => { await api.put('/pet/name', { name: editing }); setEditing(null) }, 'Renamed!')} />
                  <Btn kind="primary sm icon" aria-label="Save name" onClick={() => act(async () => { await api.put('/pet/name', { name: editing }); setEditing(null) }, 'Renamed!')}><Check size={15} /></Btn></div>)}
              <Badge>Lv {lv.level} · {lv.title}</Badge>
            </div>
            <div style={{ marginTop: 10 }}><Progress value={lv.progress} /><div className="small faint" style={{ marginTop: 4 }}>{lv.next_at ? `${lv.earned} / ${lv.next_at} tokens earned to level ${lv.level + 1}` : 'Max level reached!'}</div></div>
            <div style={{ marginTop: 16 }}><CheckinButton pet={pet} big onPat={poke} /></div>
          </Card>

          <QuestsCard pet={pet} />
          <Card delay={0.1}>
            <CardHead title="How is your wolf feeling?" sub={pet.mood.message} />
            <div style={{ height: 10, borderRadius: 10, background: 'linear-gradient(90deg, #ff5c6c, #ffb020, #4cf04c)', position: 'relative', margin: '6px 0 14px' }}>
              <motion.div animate={{ left: `${pet.mood.score}%` }} transition={{ type: 'spring', stiffness: 80 }} style={{ position: 'absolute', top: -5, width: 20, height: 20, marginLeft: -10, borderRadius: '50%', background: '#fff', border: '3px solid var(--bg-base)', boxShadow: '0 0 14px #fff' }} />
            </div>
            <ul className="muted small" style={{ paddingLeft: 18, margin: 0 }}>{pet.mood.reasons.map((r: string) => <li key={r}>{r}</li>)}</ul>
            <div className="divider" />
            <div className="row"><span className="caps">Preview moods</span>
              {MOODS.map((m) => <button key={m.key} className="btn sm icon" aria-label={m.key} style={moodPreview === m.key ? { borderColor: 'var(--glow)', background: '#2db32d22' } : undefined} onClick={() => setMoodPreview(moodPreview === m.key ? null : m.key)}>{m.emoji}</button>)}</div>
          </Card>
          <Card delay={0.15}>
            <CardHead title="Ways to earn tokens" />
            <ul className="muted small" style={{ paddingLeft: 18, margin: 0, lineHeight: 1.9 }}>
              <li>Pet your wolf once a day — streaks add up</li><li>Finish a study session (5+ min) — plus a first-session-of-the-day bonus</li>
              <li>Hit 3, 7, 14 and 30-day streaks for big bonuses</li><li>After every session, play the slot machine and the roulette</li>
              <li>Do daily quests, then open the daily and weekly chests</li><li>Learn: quizzes (up to 30), flashcards (1 per 5) and ticking off deadlines</li></ul>
            {pet.history.length > 0 && <><div className="divider" /><div className="caps" style={{ marginBottom: 6 }}>Recent</div>
              {pet.history.slice(0, 5).map((h: { t: string; amount: number; reason: string }, i: number) => <div key={i} className="row spread small"><span className="muted">{h.reason}</span><b style={{ color: h.amount < 0 ? 'var(--warning)' : 'var(--glow)' }}>{h.amount > 0 ? '+' : ''}{h.amount}</b></div>)}</>}
          </Card>
        </div>

        <Card delay={0.1}>
          <CardHead title="Wolf shop" sub="Click an item to try it on. Buying wears it right away." />
          <div className="seg" style={{ marginBottom: 18 }}>
            {tabs.map(([k, label]: string[]) => (
              <button key={k} className={tab === k ? 'on' : ''} onClick={() => { setTab(k); setPreview(null) }}>
                {tab === k && <motion.span layoutId="shoptab" className="thumb" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}<span style={{ position: 'relative' }}>{label}</span></button>))}
          </div>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))' }}>
            {items.map((it, i) => {
              const consumable = it.slot === 'consumable'
              const owned = !consumable && pet.owned.includes(it.id)
              const equipped = pet.equipped[it.slot] === it.id
              const can = pet.tokens >= it.price
              return (
                <motion.div key={it.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }} whileHover={{ y: -4 }}
                  onMouseEnter={() => it.slot !== 'upgrade' && !consumable && setPreview(it)} onMouseLeave={() => setPreview(null)}
                  style={{ padding: 12, borderRadius: 18, background: equipped ? 'var(--deep)' : 'var(--bg-base)', border: `1px solid ${equipped ? 'var(--brand)' : 'var(--border-subtle)'}`, boxShadow: equipped ? '0 0 22px #2db32d33' : 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'center', height: 136, overflow: 'hidden', borderRadius: 14, alignItems: it.slot === 'upgrade' || consumable ? 'center' : undefined }}>
                    {consumable ? <span style={{ fontSize: 56 }}>❄️</span> : it.slot === 'upgrade' ? <Sparkles size={44} color="var(--glow)" /> :
                      <Wolf mood="happy" size={136} crop={it.slot === 'back' || it.slot === 'scene' || it.slot === 'fur' ? 'full' : 'head'} animate={false}
                        equipped={{ fur: it.slot === 'fur' ? it.id : pet.equipped.fur, scene: it.slot === 'scene' ? it.id : 'scene_den', [it.slot]: it.id }} />}
                  </div>
                  {consumable && <div className="small" style={{ color: 'var(--info)' }}>Holding {pet.freezes} / 3</div>}
                  <div className="row spread" style={{ gap: 6 }}><b style={{ fontSize: 13.5 }}>{it.name}</b><Badge tone={RARITY[it.rarity]}>{it.rarity}</Badge></div>
                  <div className="small muted" style={{ minHeight: 36 }}>{it.desc}</div>
                  {owned && it.slot !== 'upgrade' ? (
                    <Btn kind={equipped ? 'sm' : 'primary sm'} onClick={() => { sfx.equip(); act(() => api.post('/pet/equip', { slot: it.slot, item: equipped && it.slot !== 'fur' && it.slot !== 'scene' ? null : it.id })) }} disabled={equipped && (it.slot === 'fur' || it.slot === 'scene')}>
                      {equipped ? (it.slot === 'fur' || it.slot === 'scene' ? 'Equipped ✓' : 'Take off') : 'Equip'}</Btn>
                  ) : owned ? <Badge>Owned ✓</Badge> : (
                    <Btn kind={can ? 'primary sm' : 'sm'} disabled={!can || (consumable && pet.freezes >= 3)} onClick={() => { sfx.buy(); act(() => api.post('/pet/buy', { item: it.id }), `${it.name} is yours!`) }}>🪙 {it.price}{can ? '' : ` · need ${it.price - pet.tokens} more`}</Btn>)}
                </motion.div>)
            })}
          </div>
        </Card>
      </div>
    </>
  )
}
