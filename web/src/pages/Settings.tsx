import { useState } from 'react'
import { Download, KeyRound, Trash2, Upload } from 'lucide-react'
import { Btn, Card, CardHead, Confirm, FilePick, Loading, PageHeader, notifyChange, useApi, useToast } from '../components/ui'
import { api } from '../api'

export default function Settings() {
  const { data, reload } = useApi('/health')
  const toast = useToast()
  const [key, setKey] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [confirm, setConfirm] = useState<'import' | 'reset' | null>(null)
  if (!data) return <Loading />
  return (
    <>
      <PageHeader title="Set" accent="tings" sub="AI key, data export and import." />
      <div className="grid cols-2">
        <Card>
          <CardHead title="Gemini API key" sub={data.ai ? 'AI features are on ✓' : 'AI is off — offline fallbacks are used'} />
          <p className="small muted">Get a free key at aistudio.google.com/apikey. It's kept in server memory for this session only; put it in <span className="kbd">.env</span> to keep it.</p>
          <div className="row" style={{ marginTop: 14 }}>
            <input className="input grow" type="password" placeholder="AIza…" value={key} onChange={(e) => setKey(e.target.value)} />
            <Btn kind="primary" icon={KeyRound} onClick={async () => { await api.put('/settings/key', { key }); setKey(''); reload(); notifyChange(); toast('Key saved') }}>Save</Btn>
          </div>
        </Card>
        <Card>
          <CardHead title="Export data" sub="Courses, sessions, calendar, quizzes and uploaded files as one .zip" />
          <a className="btn primary" href="/api/export" download><Download size={16} /> Download archive</a>
        </Card>
        <Card>
          <CardHead title="Import data" sub="Replaces everything in the app." />
          <FilePick accept=".zip" label={file ? file.name : 'Drop an archive (.zip) or click'} onFiles={(f) => setFile(f[0])} />
          <div style={{ marginTop: 14 }}><Btn kind="primary" icon={Upload} disabled={!file} onClick={() => setConfirm('import')}>Import archive</Btn></div>
          <p className="small faint" style={{ marginTop: 10 }}>Try <span className="kbd">examples/dashboard_archive/example_student_archive.zip</span></p>
        </Card>
        <Card style={{ borderColor: '#ff5c6c44' }}>
          <CardHead title="Danger zone" sub="Erase every course, session, file and grade." />
          <Btn kind="danger" icon={Trash2} onClick={() => setConfirm('reset')}>Erase all data</Btn>
        </Card>
      </div>
      <Confirm open={!!confirm} onClose={() => setConfirm(null)} label={confirm === 'import' ? 'Replace my data' : 'Erase everything'}
        text={confirm === 'import' ? 'Importing replaces all of your current data.' : 'This permanently deletes all your data. Export first if you want a backup.'}
        onYes={async () => {
          try {
            if (confirm === 'import' && file) { const f = new FormData(); f.append('file', file); await api.form('/import', f); setFile(null); toast('Archive imported') }
            else { await api.post('/reset'); toast('All data erased') }
            notifyChange()
          } catch (e) { toast((e as Error).message, true) }
        }} />
    </>
  )
}
