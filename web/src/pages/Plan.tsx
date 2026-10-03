import { useState } from 'react'
import { motion } from 'framer-motion'
import { CalendarPlus, ListChecks, Sparkles, Target } from 'lucide-react'
import { Badge, Btn, Card, CardHead, Empty, Field, Loading, PageHeader, notifyChange, useApi, useToast } from '../components/ui'
import { api, niceDate, parseISO } from '../api'

type Day = { date: string; minutes: number; focus: string; tasks: string[]; phase: string; note: string; topics: string[] }
type Topic = { name: string; summary: string; importance: string; confidence?: string | null }

export default function Plan() {
  const { data } = useApi('/state')
  const toast = useToast()
  const [testId, setTestId] = useState('')
  const [mats, setMats] = useState<string[]>([])
  const [note, setNote] = useState('')
  const [cfg, setCfg] = useState({ lead: 10, max_minutes: 120, use_ai: true })
  const [plan, setPlan] = useState<(Record<string, unknown> & { days: Day[]; topics: Topic[]; target_minutes: number; planned_minutes: number; note: string; next?: { topic: Topic; date: string | null } | null; course: string; title: string; source: string }) | null>(null)
  const [busy, setBusy] = useState(false)
  if (!data) return <Loading />
  const today = new Date().toISOString().slice(0, 10)
  const tests = data.events.filter((e: { type: string; date: string }) => ['Exam', 'Quiz'].includes(e.type) && e.date >= today)
  const id = testId || tests[0]?.id
  const test = tests.find((t: { id: string }) => t.id === id)
  const courseMats = data.materials.filter((m: { course: string }) => m.course === test?.course)

  const make = async (topics?: Topic[]) => {
    setBusy(true)
    try { setPlan(await api.post('/plan', { test_id: id, material_ids: mats, note, topics, ...cfg })) } catch (e) { toast((e as Error).message, true) }
    setBusy(false)
  }
  const setConf = (i: number, c: string) => {
    if (!plan) return
    const topics = plan.topics.map((t, j) => (j === i ? { ...t, confidence: c } : t))
    make(topics)
  }

  return (
    <>
      <PageHeader title="Study" accent="plan" sub="Pick an exam or quiz, tell us what's on it, and get a day-by-day plan that puts your weak topics first." />
      {!tests.length ? <Card><Empty icon={ListChecks} title="No upcoming exams or quizzes" text="Add one to the calendar first." to="/calendar" cta="Open calendar" /></Card> : (
        <div className="grid cols-1-2" style={{ alignItems: 'start' }}>
          <Card delay={0.05}>
            <CardHead title="Set up" />
            <div className="stack" style={{ gap: 14 }}>
              <Field label="Test"><select className="input" value={id} onChange={(e) => { setTestId(e.target.value); setMats([]); setPlan(null) }}>{tests.map((t: { id: string; course: string; title: string; date: string }) => <option key={t.id} value={t.id}>{t.course} · {t.title} · {niceDate(t.date)}</option>)}</select></Field>
              <div className="field"><label>Materials covered</label>
                {courseMats.length ? courseMats.map((m: { id: string; name: string }) => <label key={m.id} className="row small"><input type="checkbox" checked={mats.includes(m.id)} onChange={() => setMats(mats.includes(m.id) ? mats.filter((x) => x !== m.id) : [...mats, m.id])} />{m.name}</label>) : <span className="small faint">No uploads for this course yet — add some in Study materials.</span>}
              </div>
              <Field label="Topics your instructor mentioned"><textarea className="input" rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Chain rule, related rates…" /></Field>
              <Field label={`Start up to ${cfg.lead} days before`}><input type="range" min={3} max={21} value={cfg.lead} onChange={(e) => setCfg({ ...cfg, lead: +e.target.value })} /></Field>
              <Field label={`At most ${cfg.max_minutes} min per day`}><input type="range" min={30} max={240} step={15} value={cfg.max_minutes} onChange={(e) => setCfg({ ...cfg, max_minutes: +e.target.value })} /></Field>
              <label className="row small"><input type="checkbox" checked={cfg.use_ai} onChange={(e) => setCfg({ ...cfg, use_ai: e.target.checked })} /> Use AI for topics and tasks {!data.ai && <span className="faint">(no key — offline)</span>}</label>
              <Btn kind="primary" icon={Sparkles} busy={busy} onClick={() => make()}>Build my plan</Btn>
            </div>
          </Card>

          <div className="stack">
            {!plan && <Card><Empty icon={Target} title="Your plan will appear here" text="Choose a test and click Build my plan." /></Card>}
            {plan && <>
              {plan.next && (
                <Card delay={0} style={{ borderColor: '#4cf04c77', boxShadow: '0 0 50px #2db32d33' }}>
                  <div className="caps">Next up</div>
                  <h3 style={{ fontSize: 22, margin: '4px 0' }}>{plan.next.topic.name}</h3>
                  <p className="muted">{plan.next.topic.summary}</p>
                  {plan.next.date && <p className="small faint">Planned for {niceDate(plan.next.date)}</p>}
                </Card>)}
              {plan.topics.length > 0 && (
                <Card delay={0.05}>
                  <CardHead title="Topics" sub="Rate how you feel — the plan re-orders around your weak spots" />
                  <div className="stack" style={{ gap: 10 }}>
                    {plan.topics.map((t, i) => (
                      <div key={t.name} className="row spread" style={{ padding: '10px 14px', background: 'var(--bg-base)', borderRadius: 12, border: '1px solid var(--border-subtle)' }}>
                        <div className="grow"><b>{t.name}</b> <Badge tone={t.importance === 'high' ? 'danger' : t.importance === 'medium' ? 'warning' : 'mute'}>{t.importance}</Badge><div className="small muted">{t.summary}</div></div>
                        <div className="seg">{['Shaky', 'OK', 'Confident'].map((c) => <button key={c} className={t.confidence === c ? 'on' : ''} style={t.confidence === c ? { background: 'var(--brand)' } : undefined} onClick={() => setConf(i, c)}>{c}</button>)}</div>
                      </div>))}
                  </div>
                </Card>)}
              <Card delay={0.1}>
                <CardHead title={`${plan.course} · ${plan.title}`} sub={`${(plan.planned_minutes / 60).toFixed(1)} h planned of ${(plan.target_minutes / 60).toFixed(1)} h recommended · ${plan.source}`}>
                  <Btn icon={CalendarPlus} onClick={async () => { const r = await api.post('/plan/events', { course: plan.course, days: plan.days }); toast(`Added ${r.added} study sessions to the calendar`); notifyChange() }}>Add to calendar</Btn>
                </CardHead>
                {plan.note && <p style={{ color: 'var(--warning)', marginBottom: 14 }}>{plan.note}</p>}
                <div className="stack" style={{ gap: 12 }}>
                  {plan.days.map((d, i) => (
                    <motion.div key={d.date} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }} style={{ display: 'grid', gridTemplateColumns: '84px 1fr', gap: 16, padding: 16, background: 'var(--bg-base)', borderRadius: 16, border: '1px solid var(--border-subtle)' }}>
                      <div><div className="caps">{parseISO(d.date).toLocaleDateString(undefined, { weekday: 'short' })}</div><div className="num" style={{ fontSize: 26, color: 'var(--glow)' }}>{parseISO(d.date).getDate()}</div><div className="small faint">{d.minutes} min</div></div>
                      <div><b>{d.focus}</b> <Badge tone="mute">{d.phase}</Badge>
                        <ul style={{ margin: '8px 0 0', paddingLeft: 18 }} className="small muted">{d.tasks.map((t, j) => <li key={j}>{t}</li>)}</ul>
                        {d.note && <div className="small" style={{ color: 'var(--warning)', marginTop: 6 }}>{d.note}</div>}</div>
                    </motion.div>))}
                </div>
              </Card>
            </>}
          </div>
        </div>
      )}
    </>
  )
}
