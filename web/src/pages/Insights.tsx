import { Fragment, useState } from 'react'
import { motion } from 'framer-motion'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { RefreshCw } from 'lucide-react'
import { Btn, Card, CardHead, Counter, Field, Loading, PageHeader, useApi, useToast, notifyChange } from '../components/ui'
import { api, pct } from '../api'

type Node = { samples: number; risk: number; feature?: string; threshold?: number; left?: Node; right?: Node }

function TreeNode({ n, depth = 0, rule }: { n: Node; depth?: number; rule?: string }) {
  const col = n.risk >= 0.5 ? 'var(--danger)' : n.risk >= 0.3 ? 'var(--warning)' : 'var(--glow)'
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: depth * 0.12 }} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 0 }}>
      {rule && <div className="small faint" style={{ marginBottom: 6 }}>{rule}</div>}
      <div style={{ padding: '8px 12px', borderRadius: 12, background: 'var(--bg-base)', border: `1px solid ${col}`, boxShadow: `0 0 16px ${col}44`, textAlign: 'center', fontSize: 12, minWidth: 118 }}>
        <div style={{ fontWeight: 700 }}>{n.feature ? (n.feature.includes(': ') ? `${n.feature}?` : `${n.feature} ≤ ${n.threshold!.toFixed(n.threshold! < 2 ? 2 : 0)}`) : 'Leaf'}</div>
        <div style={{ color: col }}>{pct(n.risk)} at risk</div><div className="faint">{n.samples} students</div>
      </div>
      {n.left && n.right && <div style={{ display: 'flex', gap: 12, marginTop: 14, borderTop: '1px solid var(--border-strong)', paddingTop: 10 }}>
        <TreeNode n={n.left} depth={depth + 1} rule={n.feature?.includes(': ') ? 'no' : 'yes'} /><TreeNode n={n.right} depth={depth + 1} rule={n.feature?.includes(': ') ? 'yes' : 'no'} /></div>}
    </motion.div>
  )
}

export default function Insights() {
  const { data } = useApi('/insights')
  const toast = useToast()
  const [feat, setFeat] = useState('midterm_score')
  const [busy, setBusy] = useState(false)
  if (!data) return <Loading />
  const m = data.metrics
  const imp = Object.entries(data.importances as Record<string, number>).map(([k, v]) => ({ name: k, v }))
  const courses = Object.entries(data.by_course as Record<string, number>).map(([k, v]) => ({ name: k, v }))
  const cm: number[][] = m.confusion_matrix; const cmMax = Math.max(...cm.flat())
  const box = data.boxes[feat] as Record<string, number[]>
  const scale = (x: number, lo: number, hi: number) => ((x - lo) / (hi - lo || 1)) * 100
  const all = Object.values(box).flat(); const lo = Math.min(...all), hi = Math.max(...all)
  const metrics = [['Accuracy', m.accuracy * 100, '%', `${((m.accuracy - m.baseline_accuracy) * 100).toFixed(1)} pts vs baseline`], ['Precision', m.precision * 100, '%', ''], ['Recall', m.recall * 100, '%', 'at-risk students caught'], ['F1', m.f1, '', `CV ${m.cv_f1.toFixed(2)}`], ['ROC AUC', m.roc_auc, '', '']]
  return (
    <>
      <PageHeader title="Model" accent="insights" sub={`DecisionTreeClassifier tuned with 5-fold cross-validation, trained on ${data.n_train} students and tested on ${data.n_test} held-out students it never saw.`}>
        <Btn icon={RefreshCw} busy={busy} onClick={async () => { setBusy(true); await api.post('/insights/retrain'); setBusy(false); notifyChange(); toast('Model retrained') }}>Retrain</Btn>
      </PageHeader>
      <div className="grid cols-5">
        {metrics.map(([l, v, u, s], i) => <Card key={l as string} hover delay={i * 0.05}><div className="caps">{l}</div><div className="num" style={{ fontSize: 36, color: 'var(--glow)' }}><Counter value={v as number} decimals={u ? 1 : 2} suffix={u as string} /></div><div className="small faint">{s}</div></Card>)}
      </div>
      <div className="grid cols-2" style={{ marginTop: 20 }}>
        <Card delay={0.1}><CardHead title="Confusion matrix" sub="Held-out set" />
          <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr 1fr', gap: 8, alignItems: 'stretch' }}>
            <span /><div className="caps" style={{ textAlign: 'center' }}>Pred: on track</div><div className="caps" style={{ textAlign: 'center' }}>Pred: at risk</div>
            {['Actual: on track', 'Actual: at risk'].map((l, r) => <Fragment key={l}><div className="caps" style={{ alignSelf: 'center' }}>{l}</div>
              {cm[r].map((v, c) => <motion.div key={c} whileHover={{ scale: 1.04 }} style={{ padding: '26px 0', textAlign: 'center', borderRadius: 14, background: `rgba(45,179,45,${0.1 + 0.8 * (v / cmMax)})`, border: '1px solid var(--border-strong)' }}><div className="num" style={{ fontSize: 34, color: r === c ? 'var(--text)' : 'var(--text)' }}>{v}</div><div className="small" style={{ opacity: .7 }}>{r === c ? 'correct' : 'miss'}</div></motion.div>)}</Fragment>)}
          </div></Card>
        <Card delay={0.15}><CardHead title="Feature importance" sub="What the tree relies on" />
          <div style={{ height: 300 }}><ResponsiveContainer><BarChart data={imp} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid horizontal={false} stroke="#1f2d21" /><XAxis type="number" stroke="#5f7261" fontSize={11} tickLine={false} axisLine={false} /><YAxis type="category" dataKey="name" stroke="#9bae9c" fontSize={11} width={150} tickLine={false} axisLine={false} />
            <Tooltip cursor={{ fill: '#2db32d14' }} contentStyle={{ background: '#141d15', border: '1px solid #2f4532', borderRadius: 12 }} formatter={(v) => pct(Number(v), 1)} />
            <Bar dataKey="v" radius={[0, 6, 6, 0]}>{imp.map((_, i) => <Cell key={i} fill={i === 0 ? '#4cf04c' : '#2db32d'} fillOpacity={1 - i * 0.07} />)}</Bar></BarChart></ResponsiveContainer></div></Card>
      </div>
      <Card delay={0.2} style={{ marginTop: 20 }}><CardHead title="The decision tree" sub="Top three levels · green = on track, red = at risk" />
        <div style={{ overflowX: 'auto', paddingBottom: 8 }}><div style={{ display: 'flex', justifyContent: 'center', minWidth: 900 }}><TreeNode n={data.tree} /></div></div>
        <details style={{ marginTop: 14 }}><summary className="muted" style={{ cursor: 'pointer' }}>Full tree rules (text)</summary><div className="code" style={{ marginTop: 10 }}>{data.rules}</div></details></Card>
      <div className="grid cols-2" style={{ marginTop: 20 }}>
        <Card delay={0.25}><CardHead title="At-risk rate by course" sub={`${data.rows} students in the dataset`} />
          <div style={{ height: 300 }}><ResponsiveContainer><BarChart data={courses} layout="vertical" margin={{ left: 10 }}>
            <CartesianGrid horizontal={false} stroke="#1f2d21" /><XAxis type="number" tickFormatter={(v) => pct(v)} stroke="#5f7261" fontSize={11} tickLine={false} axisLine={false} /><YAxis type="category" dataKey="name" stroke="#9bae9c" fontSize={11} width={64} tickLine={false} axisLine={false} />
            <Tooltip cursor={{ fill: '#ff5c6c14' }} contentStyle={{ background: '#141d15', border: '1px solid #2f4532', borderRadius: 12 }} formatter={(v) => pct(Number(v), 1)} />
            <Bar dataKey="v" fill="#ff5c6c" radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer></div></Card>
        <Card delay={0.3}><CardHead title="Compare a feature" sub="Min · quartiles · max by outcome">
          <div style={{ width: 220 }}><Field label=""><select className="input" value={feat} onChange={(e) => setFeat(e.target.value)}>{data.numeric.map((f: string) => <option key={f} value={f}>{data.labels[f]}</option>)}</select></Field></div></CardHead>
          <div className="stack" style={{ gap: 36, marginTop: 40 }}>
            {Object.entries(box).map(([label, q], i) => { const col = i ? '#ff5c6c' : '#4cf04c'; return (
              <div key={label}><div className="small muted" style={{ marginBottom: 8 }}>{label}</div>
                <div style={{ position: 'relative', height: 34 }}>
                  <div style={{ position: 'absolute', top: 16, left: `${scale(q[0], lo, hi)}%`, width: `${scale(q[4], lo, hi) - scale(q[0], lo, hi)}%`, height: 2, background: col, opacity: .5 }} />
                  <motion.div key={feat + label} initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} style={{ transformOrigin: 'left', position: 'absolute', top: 4, height: 26, borderRadius: 8, background: `${col}33`, border: `2px solid ${col}`, left: `${scale(q[1], lo, hi)}%`, width: `${scale(q[3], lo, hi) - scale(q[1], lo, hi)}%` }} />
                  <div style={{ position: 'absolute', top: 2, width: 3, height: 30, background: col, left: `${scale(q[2], lo, hi)}%`, boxShadow: `0 0 10px ${col}` }} />
                </div>
                <div className="small faint">median {q[2]?.toFixed(1)} · range {q[0]?.toFixed(1)}–{q[4]?.toFixed(1)}</div></div>) })}
          </div></Card>
      </div>
    </>
  )
}
