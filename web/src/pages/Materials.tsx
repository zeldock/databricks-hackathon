import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, FileText, Layers, Sparkles, Trash2, Upload } from 'lucide-react'
import { Btn, Card, CardHead, Confirm, Empty, Field, FilePick, Loading, Md, PageHeader, Segmented, notifyChange, useApi, useToast } from '../components/ui'
import { api } from '../api'
import { sfx } from '../sound'
import { GraduationCap } from 'lucide-react'

type Card_ = { front: string; back: string }
type Q = { question: string; options: string[]; answer_index: number; explanation: string }

function Flashcards({ m, onSeen }: { m: { id: string; course: string; flashcards: Card_[] }; onSeen: () => void }) {
  const [i, setI] = useState(0)
  const [flip, setFlip] = useState(false)
  const toast = useToast()
  const cards = m.flashcards
  const go = (n: number) => { setFlip(false); setI((i + n + cards.length) % cards.length); sfx.click(); api.post('/flashcards/reviewed', { course: m.course, count: 1 }).then((r) => { if (r.tokens > 0) { sfx.coin(); toast(`+${r.tokens} 🪙 for reviewing flashcards`) } onSeen() }) }
  const c = cards[i]
  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div className={`flip ${flip ? 'on' : ''}`} onClick={() => setFlip(!flip)}>
        <div className="flip-in"><div className="face front">{c.front}</div><div className="face back">{c.back}</div></div>
      </div>
      <div className="row spread" style={{ marginTop: 18 }}>
        <Btn kind="icon" onClick={() => go(-1)}><ChevronLeft size={18} /></Btn>
        <span className="muted">{i + 1} / {cards.length} · click the card to flip</span>
        <Btn kind="icon" onClick={() => go(1)}><ChevronRight size={18} /></Btn>
      </div>
    </div>
  )
}

function Quiz({ m, onDone }: { m: { id: string; quiz: Q[] }; onDone: () => void }) {
  const toast = useToast()
  const [ans, setAns] = useState<(number | null)[]>(() => m.quiz.map(() => null))
  const [res, setRes] = useState<{ score: number; correct: number; total: number; reward?: { tokens: number; label: string }; review: { correct: boolean; answer_index: number; explanation: string }[] } | null>(null)
  const submit = async () => {
    if (ans.some((a) => a === null)) return toast('Answer every question first.', true)
    const r = await api.post(`/materials/${m.id}/quiz/submit`, { answers: ans }); setRes(r); onDone()
    if (r.score >= 80) sfx.win(); else sfx.oops()
    if (r.reward?.tokens) setTimeout(sfx.coin, 600)
  }
  return (
    <div className="stack" style={{ gap: 18 }}>
      {res && (
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="card" style={{ textAlign: 'center', borderColor: res.score >= 80 ? 'var(--glow)' : 'var(--warning)' }}>
          <div className="caps">Your score</div><div className="num" style={{ fontSize: 60, color: res.score >= 80 ? 'var(--glow)' : 'var(--warning)' }}>{res.score.toFixed(0)}%</div>
          <div className="muted">{res.correct} of {res.total} correct</div>
          {res.reward && <div style={{ marginTop: 8, color: res.reward.tokens ? 'var(--glow)' : 'var(--text-2)', fontWeight: 700 }}>{res.reward.tokens ? `+${res.reward.tokens} 🪙 · ${res.reward.label}` : res.reward.label}</div>}
          <div style={{ marginTop: 12 }}><Btn onClick={() => { setRes(null); setAns(m.quiz.map(() => null)) }}>Retake quiz</Btn></div>
        </motion.div>
      )}
      {m.quiz.map((q, qi) => (
        <div key={qi} className="stack" style={{ gap: 8 }}>
          <b>Q{qi + 1}. {q.question}</b>
          {q.options.map((o, oi) => {
            const r = res?.review[qi]
            const state = r ? (oi === r.answer_index ? 'right' : oi === ans[qi] ? 'wrong' : '') : ans[qi] === oi ? 'sel' : ''
            return <motion.button key={oi} whileHover={{ x: 4 }} whileTap={{ scale: 0.98 }} disabled={!!res} onClick={() => setAns(ans.map((a, j) => (j === qi ? oi : a)))}
              style={{ textAlign: 'left', padding: '12px 16px', borderRadius: 14, cursor: 'pointer', background: state === 'right' ? 'var(--forest)' : state === 'wrong' ? '#3a1219' : 'var(--bg-base)',
                border: `1.5px solid ${state === 'right' ? 'var(--glow)' : state === 'wrong' ? 'var(--danger)' : state === 'sel' ? 'var(--brand)' : 'var(--border-subtle)'}`, boxShadow: state === 'sel' ? '0 0 18px #2db32d44' : 'none' }}>{o}</motion.button>
          })}
          {res && <div className="small muted">{res.review[qi].correct ? '✅' : '❌'} {res.review[qi].explanation}</div>}
        </div>
      ))}
      {!res && <Btn kind="primary" onClick={submit}>Submit answers</Btn>}
    </div>
  )
}

export default function Materials() {
  const { data: st } = useApi('/state')
  const { data: list } = useApi('/materials')
  const toast = useToast()
  const [sel, setSel] = useState<string | null>(null)
  const [tab, setTab] = useState<'Summary' | 'Flashcards' | 'Practice quiz'>('Summary')
  const [course, setCourse] = useState('')
  const [n, setN] = useState({ cards: 10, quiz: 5 })
  const [busy, setBusy] = useState('')
  const [del, setDel] = useState(false)
  const id = sel ?? list?.[0]?.id ?? null
  const { data: m } = useApi(id ? `/materials/${id}` : null)
  if (!st || !list) return <Loading />
  if (!st.courses.length) return <><PageHeader title="Study materials" /><Card><Empty icon={GraduationCap} title="Add a course first" text="Materials are organised per course." to="/courses" cta="Add courses" /></Card></>

  const upload = async (files: File[]) => {
    const f = new FormData(); f.append('course', course || st.courses[0]); files.forEach((x) => f.append('files', x))
    setBusy('upload')
    try { const added = await api.form('/materials', f); setSel(added[added.length - 1].id); toast(`Added ${added.length} file(s)`); notifyChange() } catch (e) { toast((e as Error).message, true) }
    setBusy('')
  }
  const gen = async (kind: 'summary' | 'flashcards' | 'quiz', body?: object) => {
    setBusy(kind)
    try { await api.post(`/materials/${id}/${kind}`, body); notifyChange() } catch (e) { toast((e as Error).message, true) }
    setBusy('')
  }

  return (
    <>
      <PageHeader title="Study" accent="materials" sub="Upload notes, slides or PDFs and turn them into summaries, flashcards and practice quizzes." />
      {!st.ai && <Card style={{ marginBottom: 20, borderColor: '#ffb02055' }}><span className="muted">AI is offline — summaries and flashcards use a basic offline mode and quizzes are unavailable. Add a Gemini key in Settings for the full experience.</span></Card>}
      <div className="grid cols-1-2" style={{ alignItems: 'start' }}>
        <div className="stack">
          <Card delay={0.05}>
            <CardHead title="Upload" />
            <Field label="Course"><select className="input" value={course || st.courses[0]} onChange={(e) => setCourse(e.target.value)}>{st.courses.map((c: string) => <option key={c}>{c}</option>)}</select></Field>
            <div style={{ marginTop: 14 }}><FilePick multiple accept=".pdf,.pptx,.docx,.txt,.md" label={busy === 'upload' ? 'Reading your files…' : 'Drop PDF, PPTX, DOCX, TXT or MD'} onFiles={upload} /></div>
          </Card>
          <Card delay={0.1}>
            <CardHead title="Library" sub={`${list.length} files`} />
            {list.length ? <div className="stack" style={{ gap: 8 }}>
              {list.map((x: { id: string; name: string; course: string }) => (
                <motion.div key={x.id} whileHover={{ x: 4 }} onClick={() => setSel(x.id)} className="row" style={{ padding: '10px 12px', borderRadius: 12, cursor: 'pointer', background: x.id === id ? 'var(--forest)' : 'var(--bg-base)', border: `1px solid ${x.id === id ? 'var(--brand)' : 'var(--border-subtle)'}` }}>
                  <FileText size={18} color="var(--glow)" /><div className="grow" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{x.name}</div><span className="tag-course">{x.course}</span>
                </motion.div>))}
            </div> : <Empty icon={Upload} title="Library is empty" text="Upload your first file above." />}
          </Card>
        </div>

        <Card delay={0.15}>
          {!m ? <Empty icon={Layers} title="Pick a file" text="Choose or upload a file to study." /> : <>
            <CardHead title={m.name} sub={`${m.course} · ${(m.size / 1024).toFixed(0)} KB · ${m.chars.toLocaleString()} characters`}>
              <Btn kind="danger sm" icon={Trash2} onClick={() => setDel(true)}>Delete</Btn>
            </CardHead>
            {m.error && <p style={{ color: 'var(--warning)' }}>Couldn't read text: {m.error}</p>}
            <div style={{ marginBottom: 18 }}><Segmented options={['Summary', 'Flashcards', 'Practice quiz'] as const} value={tab} onChange={setTab} /></div>
            <AnimatePresence mode="wait">
              <motion.div key={tab + m.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                {tab === 'Summary' && <>
                  <Btn kind="primary" icon={Sparkles} busy={busy === 'summary'} onClick={() => gen('summary')}>{m.summary ? 'Regenerate' : 'Generate summary'}</Btn>
                  {m.summary && <div style={{ marginTop: 18 }}><Md text={m.summary} /><p className="small faint">Generated with {m.summary_source}</p></div>}
                </>}
                {tab === 'Flashcards' && <>
                  <div className="row" style={{ marginBottom: 20 }}><span className="small muted">Cards</span><input type="range" min={5} max={20} value={n.cards} onChange={(e) => setN({ ...n, cards: +e.target.value })} style={{ width: 180 }} /><b>{n.cards}</b>
                    <Btn kind="primary" icon={Sparkles} busy={busy === 'flashcards'} onClick={() => gen('flashcards', { n: n.cards })}>Generate</Btn></div>
                  {m.flashcards.length ? <Flashcards key={m.id + m.flashcards.length} m={m} onSeen={notifyChange} /> : <p className="muted">No flashcards yet.</p>}
                </>}
                {tab === 'Practice quiz' && <>
                  <div className="row" style={{ marginBottom: 20 }}><span className="small muted">Questions</span><input type="range" min={3} max={10} value={n.quiz} onChange={(e) => setN({ ...n, quiz: +e.target.value })} style={{ width: 180 }} /><b>{n.quiz}</b>
                    <Btn kind="primary" icon={Sparkles} busy={busy === 'quiz'} disabled={!st.ai} onClick={() => gen('quiz', { n: n.quiz })}>Generate</Btn></div>
                  {!st.ai && <p className="muted">Practice quizzes need a Gemini API key.</p>}
                  {m.quiz.length > 0 && <Quiz key={m.id + m.quiz.length} m={m} onDone={notifyChange} />}
                </>}
              </motion.div>
            </AnimatePresence>
          </>}
        </Card>
      </div>
      <Confirm open={del} onClose={() => setDel(false)} label="Delete" text="Delete this file with its summary, flashcards and quiz?"
        onYes={async () => { await api.del(`/materials/${id}`); setSel(null); notifyChange(); toast('Deleted') }} />
    </>
  )
}
