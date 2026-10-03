import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Plus, Trash2, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge, Btn, Card, CardHead, Empty, Field, FilePick, Loading, PageHeader, Segmented, notifyChange, useApi, useToast } from '../components/ui'
import Gauge, { tierInfo } from '../components/Gauge'
import { api, pct } from '../api'
import { GraduationCap } from 'lucide-react'

type Prof = Record<string, number | string | null>
type Result = { probability: number; prediction: number; tier: string; path: string[]; suggestions: { label: string; you: string; target: string; advice: string }[]; resources: string[] }
type Item = { item: string; type: string; weight: number | null; score: number | null }
const SOURCES = ['My activity', 'What-if', 'Dataset student', 'Upload a CSV'] as const

function FeatureInput({ f, meta, value, onChange, disabled }: { f: string; meta: { labels: Record<string, string>; ranges: Record<string, number[]>; percent_cols: string[] }; value: number | null; onChange: (v: number) => void; disabled?: boolean }) {
  const [lo, hi, step] = meta.ranges[f]; const isPct = meta.percent_cols.includes(f)
  const v = value ?? lo; const shown = isPct ? Math.round(v * 100) : v
  return (
    <div className="field">
      <div className="row spread"><label>{meta.labels[f]}</label>
        <input className="input" type="number" disabled={disabled} style={{ width: 84, padding: '4px 8px', textAlign: 'right' }} value={Number.isFinite(shown) ? +shown.toFixed(2) : ''} step={isPct ? 1 : step}
          onChange={(e) => onChange(isPct ? +e.target.value / 100 : +e.target.value)} />
      </div>
      <input type="range" disabled={disabled} min={lo} max={hi} step={step} value={v} onChange={(e) => onChange(+e.target.value)} style={{ opacity: disabled ? 0.4 : 1 }} />
    </div>
  )
}

function Outcome({ r, actual }: { r: Result; actual?: number | null }) {
  const t = tierInfo(r.tier)
  return (
    <div className="grid cols-1-2" style={{ alignItems: 'start' }}>
      <Card style={{ borderColor: `${t.color}55`, boxShadow: `0 0 60px ${t.color}22` }}>
        <Gauge probability={r.probability} tier={r.tier} />
        {actual != null && <p className="small muted" style={{ textAlign: 'center', marginTop: 14 }}>Actual outcome: <b>{actual ? 'D/F (at risk)' : 'C or better'}</b> — the model was {actual === r.prediction ? '✅ correct' : '❌ wrong'}.</p>}
      </Card>
      <Card>
        <CardHead title="Why the model decided this" sub="The exact splits the decision tree followed" />
        <div className="stack" style={{ gap: 8 }}>
          {r.path.map((p, i) => <motion.div key={i} initial={{ opacity: 0, x: -14 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }} className="row" style={{ padding: '10px 14px', background: 'var(--bg-base)', borderRadius: 12, border: '1px solid var(--border-subtle)' }}><span className="num" style={{ color: 'var(--glow)', fontSize: 18 }}>{i + 1}</span>{p}</motion.div>)}
        </div>
      </Card>
    </div>
  )
}

function Advice({ r }: { r: Result }) {
  return (
    <Card style={{ marginTop: 20 }}>
      <CardHead title="Suggested next steps" sub="Compared with the median on-track student" />
      {r.suggestions.length ? <div className="grid cols-2">
        {r.suggestions.map((s) => <motion.div key={s.label} whileHover={{ y: -3 }} style={{ padding: 16, background: 'var(--bg-base)', borderRadius: 16, border: '1px solid var(--border-subtle)' }}>
          <b>{s.label}</b><div className="small"><span style={{ color: 'var(--warning)' }}>you: {s.you}</span> · <span style={{ color: 'var(--glow)' }}>on-track: {s.target}</span></div><p className="muted" style={{ marginTop: 8 }}>{s.advice}</p></motion.div>)}
      </div> : <p style={{ color: 'var(--glow)' }}><CheckCircle2 size={16} style={{ verticalAlign: -3 }} /> No major gaps versus on-track students — keep it up!</p>}
      {r.resources.length > 0 && <><div className="divider" /><div className="caps">Academic support</div><ul className="muted">{r.resources.map((x) => <li key={x}>{x}</li>)}</ul></>}
    </Card>
  )
}

function GradeCalc({ course, initial, onSaved }: { course: string; initial: { items: Item[]; types: string[]; summary: Json_; check?: { tone: string; text: string } }; onSaved: () => void }) {
  const toast = useToast()
  const [items, setItems] = useState<Item[]>(initial.items)
  const [prev, setPrev] = useState<{ errors: string[]; summary: Json_ } | null>({ errors: [], summary: initial.summary })
  const first = useRef(true)
  useEffect(() => { setItems(initial.items) }, [course]) // eslint-disable-line
  useEffect(() => {
    if (first.current) { first.current = false; return }
    const t = setTimeout(() => api.post('/grades/preview', { items }).then(setPrev), 250)
    return () => clearTimeout(t)
  }, [items])
  const s = prev?.summary
  const set = (i: number, patch: Partial<Item>) => setItems(items.map((x, j) => (j === i ? { ...x, ...patch } : x)))
  const num = (v: string) => (v === '' ? null : +v)
  const toneColor = { error: 'var(--danger)', warning: 'var(--warning)', success: 'var(--glow)', info: 'var(--info)' } as Record<string, string>
  return (
    <Card>
      <CardHead title={`Your grades in ${course}`} sub="Weight and score from your syllabus. Leave the score blank if it isn't graded yet.">
        <Btn kind="sm" icon={Plus} onClick={() => setItems([...items, { item: '', type: 'Assignment', weight: null, score: null }])}>Add item</Btn>
        <Btn kind="primary sm" disabled={!!prev?.errors.length} onClick={async () => { await api.put(`/grades/${encodeURIComponent(course)}`, { items }); toast('Grades saved'); onSaved() }}>Save grades</Btn>
      </CardHead>
      <table className="table"><thead><tr><th>Item</th><th>Type</th><th>Weight %</th><th>Score %</th><th /></tr></thead><tbody>
        {items.map((it, i) => <tr key={i}>
          <td><input className="input" value={it.item} onChange={(e) => set(i, { item: e.target.value })} placeholder="Midterm 1" /></td>
          <td><select className="input" value={it.type} onChange={(e) => set(i, { type: e.target.value })}>{initial.types.map((t) => <option key={t}>{t}</option>)}</select></td>
          <td><input className="input" type="number" style={{ width: 90 }} value={it.weight ?? ''} onChange={(e) => set(i, { weight: num(e.target.value) })} /></td>
          <td><input className="input" type="number" style={{ width: 90 }} value={it.score ?? ''} onChange={(e) => set(i, { score: num(e.target.value) })} /></td>
          <td><Btn kind="ghost sm icon" onClick={() => setItems(items.filter((_, j) => j !== i))}><Trash2 size={15} /></Btn></td></tr>)}
      </tbody></table>
      {!items.length && <p className="muted" style={{ marginTop: 12 }}>No graded items yet — add assignments, quizzes and your midterm.</p>}
      {prev?.errors.map((e) => <p key={e} style={{ color: 'var(--danger)', marginTop: 10 }}><AlertTriangle size={14} style={{ verticalAlign: -2 }} /> {e}</p>)}
      {s && <>
        <div className="divider" />
        <div className="grid cols-4">
          <div><div className="caps">Current average</div><div className="num" style={{ fontSize: 30, color: 'var(--glow)' }}>{s.current != null ? `${s.current.toFixed(1)}%` : '—'}<small style={{ fontSize: 16 }}> {s.current_letter}</small></div></div>
          <div><div className="caps">Projected final</div><div className="num" style={{ fontSize: 30, color: 'var(--glow)' }}>{s.projected != null ? `${s.projected.toFixed(1)}%` : '—'}<small style={{ fontSize: 16 }}> {s.projected_letter}</small></div></div>
          <div><div className="caps">Best / worst case</div><div className="num" style={{ fontSize: 22 }}>{s.best_case.toFixed(0)}% / {s.worst_case.toFixed(0)}%</div></div>
          <div><div className="caps">Work remaining</div><div className="num" style={{ fontSize: 22 }}>{s.remaining_weight.toFixed(0)}%</div></div>
        </div>
        {s.remaining_weight > 0 && <div className="row" style={{ marginTop: 14 }}><span className="caps">Score needed on the rest for…</span>
          {Object.entries(s.needed as Record<string, number | null>).map(([g, v]) => <Badge key={g} tone={v != null && v > 100 ? 'danger' : v != null && v > 90 ? 'warning' : ''}>{g}: {v == null ? '—' : v > 100 ? 'out of reach' : `${Math.max(0, v).toFixed(0)}%`}</Badge>)}</div>}
      </>}
      {initial.check && <p style={{ marginTop: 16, padding: '12px 16px', borderRadius: 12, background: 'var(--bg-base)', border: `1px solid ${toneColor[initial.check.tone]}66`, color: toneColor[initial.check.tone] }}>{initial.check.text.replace(/\*\*/g, '')}</p>}
    </Card>
  )
}
type Json_ = { current: number | null; current_letter: string; projected: number | null; projected_letter: string; best_case: number; worst_case: number; remaining_weight: number; needed: Record<string, number | null> } | null

export default function Risk() {
  const { data: st } = useApi('/state')
  const { data: meta } = useApi('/risk/meta')
  const toast = useToast()
  const [src, setSrc] = useState<(typeof SOURCES)[number]>('My activity')
  const [course, setCourse] = useState('')
  const [student, setStudent] = useState('')
  const [whatif, setWhatif] = useState<Prof | null>(null)
  const [dsProf, setDsProf] = useState<Prof | null>(null)
  const [result, setResult] = useState<Result | null>(null)
  const [actual, setActual] = useState<number | null>(null)
  const [batch, setBatch] = useState<any>(null) // eslint-disable-line @typescript-eslint/no-explicit-any
  const c = course || st?.courses?.[0] || ''
  const { data: mine, reload } = useApi(src === 'My activity' && c ? `/risk/mine/${encodeURIComponent(c)}` : null, [c])
  const [profile, setProfile] = useState<Prof | null>(null)

  useEffect(() => { if (meta && !whatif) setWhatif({ ...meta.medians, course: meta.dataset_courses[0], class_year: 'Freshman' }) }, [meta, whatif])
  useEffect(() => { if (mine) setProfile(mine.profile) }, [mine])
  useEffect(() => {
    if (!student || src !== 'Dataset student') return
    api.get(`/risk/student/${student}`).then((r) => { setDsProf(r.profile); setActual(r.actual); setResult(r.result) })
  }, [student, src])

  // Live prediction for editable profiles.
  const editable = src === 'My activity' ? profile : src === 'What-if' ? whatif : src === 'Dataset student' ? dsProf : null
  useEffect(() => {
    if (!editable || src === 'Upload a CSV') return
    const t = setTimeout(() => api.post('/risk/predict', { profile: editable }).then(setResult), 120)
    return () => clearTimeout(t)
  }, [editable, src])

  if (!st || !meta) return <Loading />
  const setP = (f: string, v: number | string) => {
    if (src === 'My activity') setProfile({ ...profile!, [f]: v })
    else if (src === 'What-if') setWhatif({ ...whatif!, [f]: v })
    else setDsProf({ ...dsProf!, [f]: v })
  }
  const derivedKeys = mine ? Object.keys(mine.derived) : []
  const personal = ['credit_hours', 'work_hours_per_week', 'attendance_rate', 'avg_sleep_hours']
  const fields = src === 'My activity' ? personal : meta.numeric

  return (
    <>
      <PageHeader title="Risk" accent="check" sub="Your expected grade from real scores, plus a decision tree trained on the WolfHacks dataset that estimates your chance of a D or F — with reasons and next steps." >
        <Segmented options={[...SOURCES]} value={src} onChange={(v) => { setSrc(v); setResult(null); setActual(null) }} />
      </PageHeader>

      {src === 'Upload a CSV' ? (
        <>
          <Card><CardHead title="Score a whole class" sub="CSV with the model's columns. Include at_risk to see accuracy against true outcomes." />
            <FilePick accept=".csv" label="Drop a CSV or click to choose (try examples/student_csvs/heldout_students.csv)" onFiles={async (f) => { const fd = new FormData(); fd.append('file', f[0]); try { setBatch(await api.form('/risk/batch', fd)) } catch (e) { toast((e as Error).message, true) } }} /></Card>
          {batch && <>
            <div className="grid cols-4" style={{ marginTop: 20 }}>
              {[['On track', 'on_track', 'var(--glow)'], ['Watch', 'watch', 'var(--warning)'], ['At risk', 'at_risk', 'var(--danger)']].map(([l, k, col]) => <Card key={k} hover><div className="caps">{l}</div><div className="num" style={{ fontSize: 38, color: col }}>{batch.counts[k] ?? 0}</div></Card>)}
              <Card hover><div className="caps">Students</div><div className="num" style={{ fontSize: 38 }}>{batch.n}</div></Card>
            </div>
            {batch.metrics && <div className="grid cols-4" style={{ marginTop: 20 }}>{['accuracy', 'precision', 'recall', 'roc_auc'].map((k) => <Card key={k}><div className="caps">{k.replace('_', ' ')}</div><div className="num" style={{ fontSize: 32, color: 'var(--glow)' }}>{batch.metrics[k] != null ? pct(batch.metrics[k], 1) : '—'}</div></Card>)}</div>}
            <Card style={{ marginTop: 20 }}><CardHead title="Ranked by risk" sub="Top 500 students" />
              <div style={{ maxHeight: 460, overflow: 'auto' }}><table className="table"><thead><tr><th>Student</th><th>Course</th><th>Risk</th><th>Tier</th><th>Top suggestion</th></tr></thead><tbody>
                {batch.rows.map((r: { student_id?: string; course: string; risk_probability: number; risk_tier: string; top_suggestion: string }, i: number) => <tr key={i}><td>{r.student_id ?? i + 1}</td><td>{r.course}</td><td><b style={{ color: tierInfo(r.risk_tier).color }}>{pct(r.risk_probability)}</b></td><td><Badge tone={r.risk_tier === 'at_risk' ? 'danger' : r.risk_tier === 'watch' ? 'warning' : ''}>{r.risk_tier.replace('_', ' ')}</Badge></td><td className="small muted">{r.top_suggestion}</td></tr>)}
              </tbody></table></div></Card>
          </>}
        </>
      ) : (
        <>
          {src === 'My activity' && (!st.courses.length ? <Card><Empty icon={GraduationCap} title="Add a course first" text="Your risk check is calculated per course." to="/courses" cta="Go to Courses" /></Card> : (
            <div className="row" style={{ marginBottom: 20 }}><span className="caps">Course</span>
              <select className="input" style={{ width: 220 }} value={c} onChange={(e) => { setCourse(e.target.value); setResult(null) }}>{st.courses.map((x: string) => <option key={x}>{x}</option>)}</select></div>))}
          {src === 'Dataset student' && <div className="row" style={{ marginBottom: 20 }}><span className="caps">Student</span>
            <select className="input" style={{ width: 320 }} value={student} onChange={(e) => setStudent(e.target.value)}><option value="">Choose a student…</option>{meta.students.map((s: { id: string; course: string; class_year: string }) => <option key={s.id} value={s.id}>{s.id} · {s.course} · {s.class_year}</option>)}</select></div>}

          {(src !== 'My activity' || st.courses.length > 0) && editable && <>
            {src === 'My activity' && mine && <div className="stack" style={{ marginBottom: 20 }}>
              <GradeCalc key={c} course={c} initial={mine.grades} onSaved={() => { reload(); notifyChange() }} /></div>}
            {result && <Outcome r={result} actual={src === 'Dataset student' ? actual : null} />}
            {result && <Advice r={result} />}
            <Card style={{ marginTop: 20 }}>
              <CardHead title={src === 'My activity' ? 'About you' : 'Profile'} sub={src === 'My activity' ? 'Everything else is filled in from your activity.' : 'Drag or type — the prediction updates live.'}>
                {src === 'My activity' && <Btn kind="sm primary" onClick={async () => { await api.put('/profile', Object.fromEntries([...personal, 'class_year'].map((k) => [k, profile![k]]))); toast('Profile saved') }}>Save my profile</Btn>}
              </CardHead>
              <div className="grid cols-3" style={{ marginBottom: 18 }}>
                <Field label="Class year"><select className="input" value={String(editable.class_year)} onChange={(e) => setP('class_year', e.target.value)}>{meta.class_years.map((y: string) => <option key={y}>{y}</option>)}</select></Field>
                {src !== 'My activity' && <Field label="Course"><select className="input" value={String(editable.course)} onChange={(e) => setP('course', e.target.value)}>{meta.dataset_courses.map((y: string) => <option key={y}>{y}</option>)}</select></Field>}
              </div>
              <div className="grid cols-3">
                {fields.map((f: string) => <FeatureInput key={f} f={f} meta={meta} value={editable[f] as number | null} onChange={(v) => setP(f, v)} />)}
              </div>
              {src === 'My activity' && <><div className="divider" /><div className="caps">From your activity</div>
                <div className="grid cols-3" style={{ marginTop: 12 }}>{meta.numeric.filter((f: string) => !personal.includes(f)).map((f: string) =>
                  <FeatureInput key={f} f={f} meta={meta} value={editable[f] as number | null} onChange={() => {}} disabled />)}</div>
                <p className="small faint" style={{ marginTop: 10 }}>{derivedKeys.length} values are calculated from your study log, calendar and materials. <Link to="/log" style={{ color: 'var(--glow)' }}>Log more sessions →</Link></p></>}
            </Card>
          </>}
          {src === 'Dataset student' && !student && <Card><Empty icon={Upload} title="Pick a student" text="Choose a dataset student to see how the model scored them versus what actually happened." /></Card>}
        </>
      )}
    </>
  )
}
