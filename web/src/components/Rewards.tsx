import { useCallback, useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Coins, PartyPopper, Ticket, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { Json } from '../api'
import { Btn, Counter, notifyChange as notifyPet } from './ui'
import { sfx } from '../sound'
import { useMega } from '../mega'
import Wolf from './Wolf'
import { DancingCrew } from './Crew'
import SlotGame from './games/Slots'
import RouletteGame from './games/Roulette'
import PlinkoGame from './games/Plinko'
import CrossyGame from './games/Crossy'

/* ---------------------------------------------------------------- bus */
type Open = { sessionId: string; parts?: { label: string; amount: number }[]; tokens?: number }
const bus = new EventTarget()
export const openRewards = (o: Open) => bus.dispatchEvent(new CustomEvent('open', { detail: o }))

type GameId = 'slots' | 'roulette' | 'plinko' | 'crossy'
type Step = 'summary' | 'menu' | GameId | 'done'
type Win = { game: string; amount: number; label?: string }

const GAMES: { id: GameId; tag: string; en: string; icon: string; blurb: string; color: string }[] = [
  { id: 'slots', tag: 'THE CLASSIC', en: 'Wolf Slots', icon: '🎰', blurb: 'Pull the lever, match the symbols', color: '#4cf04c' },
  { id: 'roulette', tag: 'SPIN IT', en: 'Lucky Roulette', icon: '🎡', blurb: 'Spin for tokens and mystery prizes', color: '#ffb020' },
  { id: 'plinko', tag: 'DROP IT', en: 'Wolf Plinko', icon: '🎯', blurb: 'Drop a ball, hope for the edges', color: '#ff8fc7' },
  { id: 'crossy', tag: 'PUSH YOUR LUCK', en: 'Crossy Wolf', icon: '🚦', blurb: 'Hop the lanes, cash out in time', color: '#7ff0c8' },
]

function GameMenu({ pet, playsLeft, resuming, onPick }: { pet: Json; playsLeft: number; resuming: boolean; onPick: (g: GameId) => void }) {
  const mega = useMega()
  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <div style={{ position: 'absolute', right: -4, top: -6, zIndex: 1 }}><Wolf mood="ecstatic" equipped={{ hat: 'party', eyewear: 'shades', fur: 'fur_snow', scene: null }} size={88} scene={false} crop="head" animate={false} /></div>
      <div style={{ position: 'absolute', left: -4, top: 0, zIndex: 1 }}><Wolf mood="ecstatic" equipped={{ ...pet.equipped, scene: null }} size={88} scene={false} crop="head" animate={false} /></div>
      <div className="caps" style={{ color: '#ff8fc7' }}>BONUS ROUND</div>
      <h2 style={{ fontSize: 32, letterSpacing: -1, margin: '4px 0 6px' }}>Pick your <span style={{ color: 'var(--glow)' }}>game!</span></h2>
      <div className="row" style={{ justifyContent: 'center', gap: 8, marginBottom: 14 }}>
        <Ticket size={18} color="var(--warning)" />
        <b>{playsLeft} bonus play{playsLeft === 1 ? '' : 's'} left</b>
        {Array.from({ length: Math.max(playsLeft, 0) }).map((_, i) => <motion.span key={i} animate={{ scale: [1, 1.25, 1] }} transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}>🎟️</motion.span>)}
      </div>
      {mega && <div className="mega-ribbon">🎰 MEGA JACKPOT MODE ON — every game pays big! 🎰</div>}
      <div className="grid cols-2" style={{ gap: 14, position: 'relative', zIndex: 2 }}>
        {GAMES.map((g, i) => {
          const live = playsLeft > 0 || (g.id === 'crossy' && resuming)
          return (
            <motion.button key={g.id} className="game-card" disabled={!live} onMouseEnter={() => live && sfx.menuHover()} onClick={() => { sfx.menuSelect(); onPick(g.id) }}
              initial={{ opacity: 0, y: 22, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: 0.08 * i, type: 'spring', stiffness: 260, damping: 20 }}
              whileHover={live ? { y: -6, scale: 1.04, rotate: i % 2 ? 1.5 : -1.5 } : undefined} whileTap={live ? { scale: 0.96 } : undefined}
              style={{ ['--c' as string]: g.color }}>
              <span className="game-ico">{g.icon}</span>
              <span className="game-tag">{g.tag}</span>
              <b>{g.en}</b>
              <small>{g.id === 'crossy' && resuming ? 'Run in progress — continue!' : g.blurb}</small>
            </motion.button>)
        })}
      </div>
      <div className="menu-crew"><DancingCrew wolves={7} size={74} seed={2} /></div>
    </div>
  )
}

/* -------------------------------------------------------------- flow */
export function RewardHost() {
  const [open, setOpen] = useState<Open | null>(null)
  const [pet, setPet] = useState<Json>(null)
  const [step, setStep] = useState<Step>('summary')
  const [wins, setWins] = useState<Win[]>([])
  const [loadErr, setLoadErr] = useState('')

  const playsOf = (p: Json, sid: string) => p?.tickets.find((x: { session_id: string }) => x.session_id === sid)?.plays_left ?? 0
  const refresh = useCallback(async () => { const p = await api.get('/pet'); setPet(p); return p }, [])

  const start = useCallback(async (o: Open) => {
    setLoadErr(''); setWins([])
    try {
      const p = await refresh()
      setStep(o.parts ? 'summary' : playsOf(p, o.sessionId) > 0 || p.crossy_active === o.sessionId ? 'menu' : 'done')
      setOpen(o)
    } catch (e) { setLoadErr((e as Error).message) }
  }, [refresh])
  useEffect(() => {
    const h = (e: Event) => start((e as CustomEvent<Open>).detail)
    bus.addEventListener('open', h)
    return () => bus.removeEventListener('open', h)
  }, [start])

  const close = () => { setOpen(null); notifyPet() }
  const playsLeft = open ? playsOf(pet, open.sessionId) : 0
  const resuming = !!open && pet?.crossy_active === open.sessionId
  const total = (open?.tokens ?? 0) + wins.reduce((n, w) => n + w.amount, 0)
  const finished = async (game: string, r: Json) => {
    setWins((w) => [...w, { game, amount: r.amount ?? r.payout ?? 0, label: r.label }])
    const p = await refresh()
    setStep(playsOf(p, open!.sessionId) > 0 ? 'menu' : 'done')
  }
  const wide = step === 'menu' || step === 'plinko' || step === 'crossy'
  return (
    <AnimatePresence>
      {open && pet && (
        <motion.div className="modal-bg" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <motion.div className="modal" style={{ width: `min(${wide ? 700 : 620}px, 100%)`, position: 'relative', overflow: 'hidden', maxHeight: '96vh', overflowY: 'auto' }}
            initial={{ scale: 0.85, y: 40, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} transition={{ type: 'spring', stiffness: 300, damping: 26 }}>
            <button className="btn ghost sm icon" style={{ position: 'absolute', right: 14, top: 14, zIndex: 6 }} onClick={close} aria-label="Close"><X size={18} /></button>
            {loadErr && <p style={{ color: 'var(--danger)' }}>{loadErr}</p>}
            {step === 'summary' && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-end', gap: 6 }}>
                  <Wolf mood="ecstatic" equipped={{ hat: 'party', fur: 'fur_emerald', scene: null }} size={120} scene={false} animate={false} />
                  <Wolf mood="ecstatic" equipped={pet.equipped} size={190} />
                  <Wolf mood="ecstatic" equipped={{ hat: 'crown', eyewear: 'shades', fur: 'fur_golden', scene: null }} size={120} scene={false} animate={false} />
                </div>
                <div className="caps" style={{ color: '#ff8fc7', marginTop: 8 }}>NICE SESSION</div>
                <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '2px 0 4px' }}>Session <span style={{ color: 'var(--glow)' }}>complete!</span></h2>
                <p className="muted">{pet.name} is proud of you.</p>
                <div style={{ margin: '16px auto 0', maxWidth: 360, textAlign: 'left' }}>
                  {open.parts?.map((p, i) => (
                    <motion.div key={i} className="row spread" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.12 }} style={{ padding: '7px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                      <span className="muted">{p.label}</span><b style={{ color: p.amount < 0 ? 'var(--warning)' : 'var(--glow)' }}>{p.amount > 0 ? '+' : ''}{p.amount} 🪙</b>
                    </motion.div>))}
                  <div className="row spread" style={{ padding: '12px 0 0' }}><b>Total</b><span className="num" style={{ fontSize: 26, color: 'var(--glow)' }}><Counter value={open.tokens ?? 0} /> 🪙</span></div>
                </div>
                <div className="row" style={{ justifyContent: 'center', marginTop: 20 }}>
                  <Btn onClick={close}>Play later</Btn><Btn kind="primary" icon={PartyPopper} onClick={() => { sfx.yay(); setStep('menu') }}>Choose a bonus game!</Btn>
                </div>
              </div>)}
            {step === 'menu' && <GameMenu pet={pet} playsLeft={playsLeft} resuming={resuming} onPick={(g) => setStep(g)} />}
            {step === 'slots' && <SlotGame sessionId={open.sessionId} pet={pet} onDone={(r) => finished('Slots', { amount: r.payout })} />}
            {step === 'roulette' && <RouletteGame sessionId={open.sessionId} pet={pet} onDone={(r) => finished('Roulette', { amount: r.amount, label: r.prize ? r.label : '' })} />}
            {step === 'plinko' && <PlinkoGame sessionId={open.sessionId} pet={pet} onDone={(r) => finished('Plinko', { amount: r.amount })} />}
            {step === 'crossy' && <CrossyGame sessionId={open.sessionId} pet={pet} onDone={(r) => finished('Crossy', { amount: r.amount })} />}
            {step === 'done' && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><DancingCrew wolves={6} size={96} seed={5} /></div>
                <div className="caps" style={{ color: '#ff8fc7', marginTop: 6 }}>CONGRATULATIONS</div>
                <h2 style={{ fontSize: 30, letterSpacing: -1, margin: '2px 0 4px' }}>All done, <span style={{ color: 'var(--glow)' }}>nice work!</span></h2>
                <div className="num" style={{ fontSize: 44, color: 'var(--glow)' }}><Coins size={34} style={{ verticalAlign: -4 }} /> +<Counter value={total} /></div>
                <p className="muted small">{[`${open.tokens ?? 0} from studying`, ...wins.map((w) => `${w.amount} from ${w.game}${w.label ? ` (${w.label})` : ''}`)].join(' · ')}</p>
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
