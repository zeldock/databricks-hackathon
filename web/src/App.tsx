import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Award, BarChart3, CalendarDays, Coins, Flame, Volume2, VolumeX, GraduationCap, LayoutDashboard, PawPrint, Library, ListChecks, Settings as Cog, ShieldAlert, Timer,
} from 'lucide-react'
import { ToastProvider, useApi } from './components/ui'
import Dashboard from './pages/Dashboard'
import StudyLog from './pages/StudyLog'
import Calendar from './pages/Calendar'
import Plan from './pages/Plan'
import Materials from './pages/Materials'
import Risk from './pages/Risk'
import Achievements from './pages/Achievements'
import Insights from './pages/Insights'
import Courses from './pages/Courses'
import Settings from './pages/Settings'
import Den from './pages/Den'
import Wolf from './components/Wolf'
import MegaToggle from './components/MegaToggle'
import { RewardHost } from './components/Rewards'
import { cycleVolume, sfx, useVolume } from './sound'

const NAV = [
  { group: 'Overview', items: [{ to: '/', label: 'Dashboard', icon: LayoutDashboard }, { to: '/den', label: 'My wolf', icon: PawPrint }] },
  {
    group: 'Study',
    items: [
      { to: '/log', label: 'Study log', icon: Timer },
      { to: '/calendar', label: 'Calendar', icon: CalendarDays },
      { to: '/plan', label: 'Study plan', icon: ListChecks },
      { to: '/materials', label: 'Study materials', icon: Library },
    ],
  },
  {
    group: 'Insights',
    items: [
      { to: '/risk', label: 'Risk check', icon: ShieldAlert },
      { to: '/achievements', label: 'Achievements', icon: Award },
      { to: '/insights', label: 'Model insights', icon: BarChart3 },
    ],
  },
  {
    group: 'Manage',
    items: [
      { to: '/courses', label: 'Courses', icon: GraduationCap },
      { to: '/settings', label: 'Settings', icon: Cog },
    ],
  },
]

function Sidebar() {
  const { data } = useApi('/dashboard')
  const { data: pet } = useApi('/pet')
  const streak = data?.kpis.streak ?? 0
  const vol = useVolume()
  const risk = pet?.streak_risk
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><img src="/logo.png" alt="Wolf Tracks paw" /></div>
        <div>
          <div className="brand-name">Wolf <b>Tracks</b></div>
          <div className="brand-sub">Study smarter</div>
        </div>
      </div>
      {NAV.map((g) => (
        <div key={g.group}>
          <div className="nav-group">{g.group}</div>
          {g.items.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              {({ isActive }) => (
                <>
                  {isActive && <motion.span layoutId="navbar" className="pill-bar" transition={{ type: 'spring', stiffness: 400, damping: 32 }} />}
                  <Icon size={19} />{label}
                </>
              )}
            </NavLink>
          ))}
        </div>
      ))}
      <div className="side-foot">
        {pet && (
          <NavLink to="/den" className="row" style={{ gap: 10, marginBottom: 12, paddingBottom: 12, borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ width: 46, height: 46, borderRadius: 14, overflow: 'hidden', flex: 'none' }}><Wolf mood={pet.mood.key} equipped={pet.equipped} size={46} crop="head" animate={false} /></div>
            <div className="grow"><div style={{ fontWeight: 700, lineHeight: 1.2 }}>{pet.name}</div>
              <div className="small" style={{ color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 4 }}><Coins size={13} /> {pet.tokens}{pet.checkin.available && <span className="pulse" style={{ color: 'var(--glow)', marginLeft: 6 }}>● pat me!</span>}</div></div>
          </NavLink>)}
        <div className="streak"><Flame size={20} color={risk?.at_risk && streak >= 2 ? 'var(--warning)' : 'var(--glow)'} className={streak ? 'pulse' : ''} /> {streak}-day streak</div>
        <small>{risk?.at_risk && streak >= 2 ? `Ends in ${Math.floor(risk.hours_left)}h — study to save it` : streak ? 'Keep the pack moving.' : 'Log a session to start one.'}</small>
        <button className="btn ghost sm" style={{ marginTop: 8, padding: '4px 8px' }} aria-label={`Sound: ${vol}. Click to change`} onClick={() => { cycleVolume(); setTimeout(sfx.ching, 60) }}>{vol === 'off' ? <VolumeX size={15} /> : <Volume2 size={15} />} Sound: {vol === 'insane' ? 'INSANE' : vol === 'loud' ? 'Loud' : vol === 'normal' ? 'Normal' : 'Off'}</button>
      </div>
    </aside>
  )
}

function AnimatedRoutes() {
  const loc = useLocation()
  return (
    <AnimatePresence mode="wait">
      <motion.main key={loc.pathname} className="main"
        initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}>
        <Routes location={loc}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/den" element={<Den />} />
          <Route path="/log" element={<StudyLog />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/plan" element={<Plan />} />
          <Route path="/materials" element={<Materials />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/achievements" element={<Achievements />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/courses" element={<Courses />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </motion.main>
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <div className="aurora"><i /></div>
        <div className="grain" />
        <div className="shell">
          <Sidebar />
          <AnimatedRoutes />
        </div>
        <RewardHost />
        <MegaToggle />
      </ToastProvider>
    </BrowserRouter>
  )
}

