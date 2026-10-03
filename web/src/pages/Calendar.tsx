import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CalendarDays, ChevronLeft, ChevronRight, Plus, Sparkles, Trash2 } from 'lucide-react'
import { Btn, Card, CardHead, Empty, Field, FilePick, Loading, Modal, PageHeader, Segmented, notifyChange, useApi, useToast } from '../components/ui'
import { api, iso, parseISO } from '../api'
import { sfx } from '../sound'
import { GraduationCap } from 'lucide-react'

const TYPES = ['Exam', 'Deadline', 'Quiz', 'Milestone', 'Study']
type Ev = { id: string; title: string; course: string; date: string; type: string; done: boolean }

export default function Calendar() {
  const { data } = useApi('/state')
  const toast = useToast()
  const [cursor, setCursor] = useState(() => { const d = new Date(); d.setDate(1); return d })
  const [view, setView] = useState<'Month' | 'Week'>('Month')
  const [week, setWeek] = useState(() => { const d = new Date(); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d })
  const [adding, setAdding] = useState<string | null>(null)
  const [form, setForm] = useState({ title: '', course: '', type: 'Deadline' })
  const [picked, setPicked] = useState<Ev | null>(null)
  const [syl, setSyl] = useState<{ open: boolean; course: string; busy: boolean; rows: (Ev & { add: boolean })[] | null }>({ open: false, course: '', busy: false, rows: null })

  if (!data) return <Loading />
  if (!data.courses.length) return <><PageHeader title="Calendar" /><Card><Empty icon={GraduationCap} title="Add a course first" text="Events belong to a course." to="/courses" cta="Add courses" /></Card></>
  const byDay: Record<string, Ev[]> = {}
  data.events.forEach((e: Ev) => (byDay[e.date] ||= []).push(e))
  const todayISO = iso(new Date())

  const days: Date[] = []
  if (view === 'Month') {
    const first = new Date(cursor); first.setDate(1 - ((first.getDay() + 6) % 7))
    for (let i = 0; i < 42; i++) { const d = new Date(first); d.setDate(first.getDate() + i); days.push(d) }
  } else for (let i = 0; i < 7; i++) { const d = new Date(week); d.setDate(week.getDate() + i); days.push(d) }

  const shift = (n: number) => {
    if (view === 'Month') setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + n, 1))
    else { const d = new Date(week); d.setDate(d.getDate() + 7 * n); setWeek(d) }
  }
  const title = view === 'Month' ? cursor.toLocaleString(undefined, { month: 'long', year: 'numeric' }) : `Week of ${week.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`

  const create = async () => {
    try { await api.post('/events', { ...form, course: form.course || data.courses[0], date: adding }); toast('Event added'); setAdding(null); setForm({ ...form, title: '' }); notifyChange() }
    catch (e) { toast((e as Error).message, true) }
  }
  const readSyllabus = async (files: File[]) => {
    const f = new FormData(); f.append('course', syl.course || data.courses[0]); f.append('file', files[0])
    setSyl({ ...syl, busy: true })
    try { const rows = await api.form('/syllabus', f); setSyl({ ...syl, busy: false, rows: rows.map((r: Ev) => ({ ...r, add: true })) }) }
    catch (e) { toast((e as Error).message, true); setSyl({ ...syl, busy: false }) }
  }
  const addSyllabus = async () => {
    const chosen = syl.rows!.filter((r) => r.add)
    for (const r of chosen) await api.post('/events', { title: r.title, course: syl.course || data.courses[0], date: r.date, type: r.type })
    toast(`Added ${chosen.length} events`); setSyl({ open: false, course: '', busy: false, rows: null }); notifyChange()
  }
  const sessionsOn = (key: string) => data.sessions.filter((s: { start: string }) => s.start.startsWith(key))

  return (
    <>
      <PageHeader title="Calendar" sub="Exams, deadlines and quizzes in one place. Click a day to add one; click an event to tick it off.">
        <Btn icon={Sparkles} onClick={() => setSyl({ ...syl, open: true, rows: null })}>Import from syllabus</Btn>
      </PageHeader>
      <Card>
        <CardHead title={title}>
          <Segmented options={['Month', 'Week'] as const} value={view} onChange={setView} />
          <Btn kind="sm icon" onClick={() => shift(-1)}><ChevronLeft size={16} /></Btn>
          <Btn kind="sm" onClick={() => { const n = new Date(); setCursor(new Date(n.getFullYear(), n.getMonth(), 1)); const w = new Date(); w.setDate(w.getDate() - ((w.getDay() + 6) % 7)); setWeek(w) }}>Today</Btn>
          <Btn kind="sm icon" onClick={() => shift(1)}><ChevronRight size={16} /></Btn>
        </CardHead>
        <AnimatePresence mode="wait">
          <motion.div key={title + view} className="cal" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.25 }}>
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => <div key={d} className="dow">{d}</div>)}
            {days.map((d) => {
              const key = iso(d); const evs = byDay[key] ?? []; const out = view === 'Month' && d.getMonth() !== cursor.getMonth()
              return (
                <div key={key} className={`day ${out ? 'out' : ''} ${key === todayISO ? 'today' : ''}`} style={view === 'Week' ? { minHeight: 200 } : undefined} onClick={() => setAdding(key)}>
                  <div className="d">{d.getDate()}</div>
                  {evs.map((e) => <div key={e.id} className={`chip ${e.type} ${e.done ? 'done' : ''}`} title={`${e.course} · ${e.title}`} onClick={(ev) => { ev.stopPropagation(); setPicked(e) }}>{e.title}</div>)}
                  {view === 'Week' && sessionsOn(key).map((s: { id: string; course: string; minutes: number }) => <div key={s.id} className="small faint">⏱ {s.course} · {Math.round(s.minutes)}m</div>)}
                </div>
              )
            })}
          </motion.div>
        </AnimatePresence>
      </Card>

      <Modal open={!!adding} onClose={() => setAdding(null)}>
        <h3>Add to {adding && parseISO(adding).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</h3>
        <div className="stack" style={{ gap: 14, marginTop: 14 }}>
          <Field label="Title"><input className="input" autoFocus value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Midterm 1" /></Field>
          <div className="grid cols-2" style={{ gap: 14 }}>
            <Field label="Course"><select className="input" value={form.course || data.courses[0]} onChange={(e) => setForm({ ...form, course: e.target.value })}>{data.courses.map((c: string) => <option key={c}>{c}</option>)}</select></Field>
            <Field label="Type"><select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>{TYPES.map((t) => <option key={t}>{t}</option>)}</select></Field>
          </div>
        </div>
        <div className="row" style={{ marginTop: 22, justifyContent: 'flex-end' }}><Btn onClick={() => setAdding(null)}>Cancel</Btn><Btn kind="primary" icon={Plus} onClick={create}>Add event</Btn></div>
      </Modal>

      <Modal open={!!picked} onClose={() => setPicked(null)}>
        {picked && <>
          <span className={`chip ${picked.type}`}>{picked.type}</span>
          <h3 style={{ marginTop: 10 }}>{picked.title}</h3>
          <p className="muted">{picked.course} · {parseISO(picked.date).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p>
          <div className="row" style={{ marginTop: 22, justifyContent: 'space-between' }}>
            <Btn kind="danger" icon={Trash2} onClick={async () => { await api.del(`/events/${picked.id}`); setPicked(null); notifyChange() }}>Delete</Btn>
            <Btn kind="primary" onClick={async () => { const r = await api.patch(`/events/${picked.id}`, { done: !picked.done }); setPicked(null); notifyChange(); if (r.tokens > 0) { sfx.coin(); toast(`Nice work! +${r.tokens} 🪙 for finishing on time`) } }}>{picked.done ? 'Mark not done' : 'Mark complete'}</Btn>
          </div>
        </>}
      </Modal>

      <Modal open={syl.open} onClose={() => setSyl({ ...syl, open: false })}>
        <h3>Import dates from a syllabus</h3>
        <p className="muted small">Gemini reads the syllabus and lists every dated item. Needs an API key in Settings.</p>
        <div className="stack" style={{ gap: 14, marginTop: 14 }}>
          <Field label="Course"><select className="input" value={syl.course || data.courses[0]} onChange={(e) => setSyl({ ...syl, course: e.target.value })}>{data.courses.map((c: string) => <option key={c}>{c}</option>)}</select></Field>
          {!syl.rows && <FilePick accept=".pdf,.docx,.pptx,.txt,.md" label={syl.busy ? 'Reading the syllabus…' : 'Drop a syllabus or click to choose'} onFiles={readSyllabus} />}
          {syl.rows && <>
            <div style={{ maxHeight: 280, overflow: 'auto' }}>
              {syl.rows.map((r, i) => <label key={i} className="row" style={{ padding: '6px 0' }}><input type="checkbox" checked={r.add} onChange={() => setSyl({ ...syl, rows: syl.rows!.map((x, j) => (j === i ? { ...x, add: !x.add } : x)) })} /><span className="grow">{r.title}</span><span className={`chip ${r.type}`}>{r.type}</span><span className="small faint">{r.date}</span></label>)}
            </div>
            <Btn kind="primary" icon={CalendarDays} onClick={addSyllabus}>Add selected</Btn>
          </>}
        </div>
      </Modal>
    </>
  )
}
