import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { GraduationCap, Pencil, Plus, Trash2 } from 'lucide-react'
import { Btn, Card, CardHead, Confirm, Empty, Loading, Modal, PageHeader, notifyChange, useApi, useToast } from '../components/ui'
import { api } from '../api'

const QUICK = ['BIO 181', 'CH 101', 'CSC 216', 'EC 201', 'ECE 200', 'ENG 101', 'MA 141', 'PY 205']

export default function Courses() {
  const { data } = useApi('/courses')
  const toast = useToast()
  const [name, setName] = useState('')
  const [rename, setRename] = useState<{ old: string; name: string } | null>(null)
  const [del, setDel] = useState<{ name: string; usage: Record<string, number> } | null>(null)
  if (!data) return <Loading />
  const run = async (fn: () => Promise<{ message: string }>) => {
    try { toast((await fn()).message); notifyChange() } catch (e) { toast((e as Error).message, true) }
  }
  const add = (n: string) => run(async () => { const r = await api.post('/courses', { name: n }); setName(''); return r })
  return (
    <>
      <PageHeader title="Your" accent="courses" sub="Everything — sessions, deadlines, materials and risk checks — is organised per course." />
      <Card>
        <CardHead title="Add a course" />
        <div className="row"><input className="input grow" style={{ maxWidth: 360 }} placeholder="e.g. MA 141" value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && add(name)} />
          <Btn kind="primary" icon={Plus} onClick={() => add(name)}>Add</Btn></div>
        <div className="row" style={{ marginTop: 14 }}>
          <span className="small faint">Quick add:</span>
          {QUICK.filter((q) => !data.some((c: { name: string }) => c.name === q)).map((q) => <Btn key={q} kind="sm" onClick={() => add(q)}>{q}</Btn>)}
        </div>
      </Card>
      <div className="grid cols-3" style={{ marginTop: 20 }}>
        <AnimatePresence>
          {data.map((c: { name: string; usage: Record<string, number> }, i: number) => (
            <motion.div key={c.name} layout initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }} transition={{ delay: i * 0.04 }}>
              <Card hover>
                <div className="row spread"><h3>{c.name}</h3>
                  <div className="row" style={{ gap: 4 }}><Btn kind="ghost sm icon" onClick={() => setRename({ old: c.name, name: c.name })}><Pencil size={15} /></Btn>
                    <Btn kind="ghost sm icon" onClick={() => setDel(c)}><Trash2 size={15} /></Btn></div></div>
                <div className="grid cols-2 small muted" style={{ gap: 6, marginTop: 14 }}>
                  <span>⏱ {c.usage.hours.toFixed(1)} h</span><span>📚 {c.usage.sessions} sessions</span>
                  <span>📅 {c.usage.events} events</span><span>📄 {c.usage.materials} files</span>
                </div>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      {!data.length && <Card style={{ marginTop: 20 }}><Empty icon={GraduationCap} title="No courses yet" text="Add the classes you're taking above." /></Card>}
      <Modal open={!!rename} onClose={() => setRename(null)}>
        <h3>Rename {rename?.old}</h3>
        <input className="input" style={{ marginTop: 12 }} autoFocus value={rename?.name ?? ''} onChange={(e) => setRename(rename && { ...rename, name: e.target.value })} />
        <div className="row" style={{ marginTop: 22, justifyContent: 'flex-end' }}><Btn onClick={() => setRename(null)}>Cancel</Btn>
          <Btn kind="primary" onClick={() => { const r = rename!; setRename(null); run(() => api.put(`/courses/${encodeURIComponent(r.old)}`, { name: r.name })) }}>Rename</Btn></div>
      </Modal>
      <Confirm open={!!del} onClose={() => setDel(null)} label="Remove course"
        text={del && `Removing ${del.name} deletes ${del.usage.sessions} sessions, ${del.usage.events} events, ${del.usage.materials} files and ${del.usage.quizzes} quiz results.`}
        onYes={() => run(() => api.del(`/courses/${encodeURIComponent(del!.name)}`))} />
    </>
  )
}
