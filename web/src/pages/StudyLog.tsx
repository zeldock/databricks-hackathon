import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Pause, Play, Plus, Square, Trash2 } from 'lucide-react'
import { Btn, Card, CardHead, Empty, Field, Loading, PageHeader, courseColor, notifyChange, useApi, useToast } from '../components/ui'
import { api, iso, niceDate } from '../api'
import { openRewards } from '../components/Rewards'
import { GraduationCap } from 'lucide-react'

type Timer = { course: string; notes: string; accum: number; startedAt: number | null; first: number }
const KEY = 'wolf-tracks-timer'
const load = (): Timer | null => { try { return JSON.parse(localStorage.getItem(KEY) || 'null') } catch { return null } }
const localISO = (d: Date) => `${iso(d)}T${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
const fmt = (s: number) => [Math.floor(s / 3600), Math.floor(s / 60) % 60, Math.floor(s) % 60].map((n) => String(n).padStart(2, '0')).join(':')

export default function StudyLog() {
  const { data } = useApi('/state')
  const toast = useToast()
  const [timer, setTimer] = useState<Timer | null>(load)
  const [, force] = useState(0)
  const [course, setCourse] = useState('')
  const [notes, setNotes] = useState('')
  const [manual, setManual] = useState({ course: '', date: iso(new Date()), time: '19:00', minutes: 45, notes: '' })
  const raf = useRef<number>(0)

  useEffect(() => {
    raf.current = window.setInterval(() => force((n) => n + 1), 500)
    return () => clearInterval(raf.current)
  }, [])
  useEffect(() => { timer ? localStorage.setItem(KEY, JSON.stringify(timer)) : localStorage.removeItem(KEY) }, [timer])

  if (!data) return <Loading />
  if (!data.courses.length) return <><PageHeader title="Study" accent="log" /><Card><Empty icon={GraduationCap} title="Add a course first" text="Sessions are tracked per course." to="/courses" cta="Add courses" /></Card></>
  const sel = course || data.courses[0]
  const elapsed = timer ? timer.accum + (timer.startedAt ? (Date.now() - timer.startedAt) / 1000 : 0) : 0
  const running = !!timer?.startedAt

  const start = () => setTimer({ course: sel, notes, accum: 0, startedAt: Date.now(), first: Date.now() })
  const pause = () => timer && setTimer({ ...timer, accum: elapsed, startedAt: null })
  const resume = () => timer && setTimer({ ...timer, startedAt: Date.now() })
  const stop = async () => {
    if (!timer) return
    const minutes = Math.max(0.5, elapsed / 60)
    try {
      const s = await api.post('/sessions', { course: timer.course, minutes, notes: timer.notes, start: localISO(new Date(timer.first)) })
      toast(`Logged ${minutes.toFixed(0)} min of ${timer.course}`); setTimer(null); notifyChange()
      if (s.reward) openRewards({ sessionId: s.id, parts: s.reward.parts, tokens: s.reward.tokens })
    } catch (e) { toast((e as Error).message, true) }
  }
  const add = async () => {
    try {
      const s = await api.post('/sessions', { course: manual.course || sel, minutes: manual.minutes, notes: manual.notes, start: `${manual.date}T${manual.time}:00` })
      toast('Session added'); notifyChange()
      if (s.reward) openRewards({ sessionId: s.id, parts: s.reward.parts, tokens: s.reward.tokens })
    } catch (e) { toast((e as Error).message, true) }
  }

  // last 30 days chart
  const days: { label: string; [c: string]: number | string }[] = []
  for (let i = 29; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i)
    const key = iso(d); const row: { label: string; [c: string]: number | string } = { label: niceDate(key) }
    data.courses.forEach((c: string) => { row[c] = 0 })
    data.sessions.filter((s: { start: string }) => s.start.startsWith(key)).forEach((s: { course: string; minutes: number }) => { row[s.course] = (row[s.course] as number) + s.minutes / 60 })
    days.push(row)
  }
  const recent = [...data.sessions].reverse().slice(0, 40)

  return (
    <>
      <PageHeader title="Study" accent="log" sub="Start the timer when you sit down to study — every minute fills in your activity grid." />
      <div className="grid cols-2">
        <Card delay={0.05} style={running ? { borderColor: '#4cf04c88', boxShadow: '0 0 60px #2db32d44' } : undefined}>
          <CardHead title="Live timer" sub={timer ? `${timer.course}${running ? ' · running' : ' · paused'}` : 'Pick a course and go'} />
          <div style={{ textAlign: 'center', padding: '10px 0 22px' }}>
            <motion.div className="timer-big" animate={{ scale: running ? [1, 1.015, 1] : 1 }} transition={{ repeat: Infinity, duration: 2 }}>{fmt(elapsed)}</motion.div>
          </div>
          {!timer ? (
            <div className="stack" style={{ gap: 14 }}>
              <Field label="Course"><select className="input" value={sel} onChange={(e) => setCourse(e.target.value)}>{data.courses.map((c: string) => <option key={c}>{c}</option>)}</select></Field>
              <Field label="What are you working on? (optional)"><input className="input" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Chapter 4 problems" /></Field>
              <Btn kind="primary" icon={Play} onClick={start}>Start timer</Btn>
            </div>
          ) : (
            <div className="row" style={{ justifyContent: 'center' }}>
              {running ? <Btn icon={Pause} onClick={pause}>Pause</Btn> : <Btn kind="primary" icon={Play} onClick={resume}>Resume</Btn>}
              <Btn kind="primary" icon={Square} onClick={stop}>Finish &amp; save</Btn>
              <Btn kind="danger" icon={Trash2} onClick={() => setTimer(null)}>Discard</Btn>
            </div>
          )}
        </Card>

        <Card delay={0.1}>
          <CardHead title="Add a past session" sub="Forgot to start the timer? Log it here." />
          <div className="grid cols-2" style={{ gap: 14 }}>
            <Field label="Course"><select className="input" value={manual.course || sel} onChange={(e) => setManual({ ...manual, course: e.target.value })}>{data.courses.map((c: string) => <option key={c}>{c}</option>)}</select></Field>
            <Field label="Minutes"><input className="input" type="number" min={1} value={manual.minutes} onChange={(e) => setManual({ ...manual, minutes: +e.target.value })} /></Field>
            <Field label="Date"><input className="input" type="date" value={manual.date} onChange={(e) => setManual({ ...manual, date: e.target.value })} /></Field>
            <Field label="Start time"><input className="input" type="time" value={manual.time} onChange={(e) => setManual({ ...manual, time: e.target.value })} /></Field>
          </div>
          <Field label="Notes"><input className="input" value={manual.notes} onChange={(e) => setManual({ ...manual, notes: e.target.value })} /></Field>
          <div style={{ marginTop: 16 }}><Btn icon={Plus} onClick={add}>Add session</Btn></div>
        </Card>
      </div>

      <Card delay={0.15} style={{ marginTop: 20 }}>
        <CardHead title="Last 30 days" sub="Hours per day" />
        <div style={{ height: 260 }}>
          <ResponsiveContainer>
            <BarChart data={days}>
              <CartesianGrid vertical={false} stroke="#1f2d21" />
              <XAxis dataKey="label" stroke="#5f7261" tickLine={false} axisLine={false} fontSize={11} interval={4} />
              <YAxis stroke="#5f7261" tickLine={false} axisLine={false} fontSize={11} />
              <Tooltip cursor={{ fill: '#2db32d14' }} contentStyle={{ background: '#141d15', border: '1px solid #2f4532', borderRadius: 12 }} formatter={(v) => Number(v).toFixed(1)} />
              {data.courses.map((c: string) => <Bar key={c} dataKey={c} stackId="a" fill={courseColor(data.courses, c)} />)}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card delay={0.2} style={{ marginTop: 20 }}>
        <CardHead title="History" sub={`${data.sessions.length} sessions`} />
        {recent.length ? (
          <table className="table"><thead><tr><th>Date</th><th>Course</th><th>Minutes</th><th>Notes</th><th /></tr></thead>
            <tbody><AnimatePresence initial={false}>
              {recent.map((s: { id: string; start: string; course: string; minutes: number; notes: string }) => (
                <motion.tr key={s.id} layout exit={{ opacity: 0, x: 40 }}>
                  <td>{niceDate(s.start)} <span className="faint small">{s.start.slice(11, 16)}</span></td>
                  <td><span className="tag-course">{s.course}</span></td><td>{s.minutes.toFixed(0)}</td><td className="muted">{s.notes}</td>
                  <td style={{ textAlign: 'right' }}><Btn kind="ghost sm icon" onClick={async () => { await api.del(`/sessions/${s.id}`); notifyChange() }}><Trash2 size={15} /></Btn></td>
                </motion.tr>
              ))}</AnimatePresence></tbody></table>
        ) : <p className="muted">No sessions yet.</p>}
      </Card>
    </>
  )
}
