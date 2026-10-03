import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Award, CheckCircle2, Circle, Clock, Flame, Layers, Sparkles } from 'lucide-react'
import { Badge, Btn, Card, CardHead, Empty, Loading, PageHeader, Progress, Stat, courseColor, useApi } from '../components/ui'
import { niceDate, parseISO, pct } from '../api'
import { tierInfo } from '../components/Gauge'
import Wolf from '../components/Wolf'
import { CheckinButton } from './Den'
import { openRewards } from '../components/Rewards'
import { QuestsCard, StreakAlert } from '../components/Quests'

export default function Dashboard() {
  const { data, error } = useApi('/dashboard')
  const { data: pet } = useApi('/pet')
  if (error) return <p className="muted">Can't reach the API: {error}. Is <span className="kbd">uvicorn api:app</span> running?</p>
  if (!data) return <Loading />
  const k = data.kpis
  const stepsDone = data.steps.filter((s: { done: boolean }) => s.done).length
  const weeks = data.weekly.map((w: Record<string, number | string>) => ({ ...w, label: niceDate(String(w.week)) }))
  // Group the 53-week grid by weeks (columns) for month labels.
  const months: { i: number; m: string }[] = []
  data.grid.forEach((c: { date: string }, i: number) => {
    const d = parseISO(c.date)
    if (i % 7 === 0 && d.getDate() <= 7) months.push({ i: i / 7, m: d.toLocaleString(undefined, { month: 'short' }) })
  })
  return (
    <>
      <PageHeader title="Welcome back," accent="pack leader." sub="Your courses, study time and risk outlook in one place." />
      {stepsDone < data.steps.length && (
        <Card className="" delay={0.05} style={{ marginBottom: 20, borderColor: '#2db32d55' }}>
          <CardHead title="Getting started" sub={`${stepsDone} of ${data.steps.length} steps complete`} />
          <Progress value={stepsDone / data.steps.length} />
          <div className="grid cols-4" style={{ marginTop: 18 }}>
            {data.steps.map((s: { label: string; done: boolean; page: string }) => (
              <Link key={s.label} to={s.page === 'log' ? '/log' : `/${s.page}`} className="row" style={{ color: s.done ? 'var(--text-3)' : 'var(--text)' }}>
                {s.done ? <CheckCircle2 size={18} color="var(--glow)" /> : <Circle size={18} color="var(--text-3)" />}
                <span style={{ textDecoration: s.done ? 'line-through' : 'none' }}>{s.label}</span>
              </Link>
            ))}
          </div>
          <p className="small faint" style={{ marginTop: 14 }}>Just exploring? Settings → Import data → <span className="kbd">examples/dashboard_archive/example_student_archive.zip</span></p>
        </Card>
      )}

      {pet && <StreakAlert pet={pet} />}
      {pet && (
        <Card delay={0.05} style={{ marginBottom: 20, padding: 18 }}>
          <div className="row" style={{ gap: 22, flexWrap: 'wrap' }}>
            <Link to="/den" style={{ flex: 'none' }}><Wolf mood={pet.mood.key} equipped={pet.equipped} size={150} crop="head" /></Link>
            <div className="grow" style={{ minWidth: 240 }}>
              <div className="row spread"><h3 style={{ fontSize: 22 }}>{pet.name} <span className="faint small">Lv {pet.level.level} {pet.level.title}</span></h3><Badge tone="warning">🪙 {pet.tokens}</Badge></div>
              <p className="muted" style={{ margin: '6px 0 14px' }}>{pet.mood.message}</p>
              <div className="row"><CheckinButton pet={pet} />
                {pet.tickets.length > 0 && <Btn kind="primary" onClick={() => openRewards({ sessionId: pet.tickets[0].session_id })}>🎰 Play bonus round</Btn>}
                <Link to="/den" className="btn">Visit the den</Link></div>
            </div>
          </div>
        </Card>)}
      {pet && <div style={{ marginBottom: 20 }}><QuestsCard pet={pet} compact /></div>}
      <div className="grid cols-4">
        <Stat label="This week" value={k.week_hours} decimals={1} unit="hrs" icon={Clock} delay={0.05} />
        <Stat label="All time" value={k.total_hours} decimals={1} unit="hrs" icon={Layers} delay={0.1} />
        <Stat label="Current streak" value={k.streak} unit={`days · best ${k.longest_streak}`} icon={Flame} delay={0.15} />
        <Stat label="Achievements" value={k.badges_unlocked} unit={`/ ${k.badges_total}`} icon={Award} delay={0.2} />
      </div>

      <div className="stack" style={{ marginTop: 20 }}>
        <Card delay={0.25}>
          <CardHead title="Study activity" sub="Every square is a day. The brighter the green, the longer you studied." />
          <div style={{ overflowX: 'auto', paddingBottom: 6 }}>
            <div style={{ minWidth: 760 }}>
              <div style={{ position: 'relative', height: 16, marginBottom: 6 }}>
                {months.map((m) => <span key={m.i} className="faint small" style={{ position: 'absolute', left: `${(m.i / 53) * 100}%` }}>{m.m}</span>)}
              </div>
              <div className="heat">
                {data.grid.map((c: { date: string; minutes: number; level: number }, i: number) => (
                  <motion.div key={c.date} className={`cell l${c.level}`} title={`${niceDate(c.date)} · ${Math.round(c.minutes)} min`}
                    initial={{ opacity: 0, scale: 0.3 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 + i * 0.0012, duration: 0.3 }} />
                ))}
              </div>
            </div>
          </div>
        </Card>

        <div className="grid cols-2-1">
          <Card delay={0.3}>
            <CardHead title="Hours per week" sub="Last 12 weeks, stacked by course" />
            {data.courses.length ? (
              <div style={{ height: 290 }}>
                <ResponsiveContainer>
                  <BarChart data={weeks}>
                    <CartesianGrid vertical={false} stroke="#1f2d21" />
                    <XAxis dataKey="label" stroke="#5f7261" tickLine={false} axisLine={false} fontSize={11} />
                    <YAxis stroke="#5f7261" tickLine={false} axisLine={false} fontSize={11} />
                    <Tooltip cursor={{ fill: '#2db32d14' }} contentStyle={{ background: '#141d15', border: '1px solid #2f4532', borderRadius: 12 }} />
                    {data.courses.map((c: string) => <Bar key={c} dataKey={c} stackId="a" fill={courseColor(data.courses, c)} radius={[3, 3, 0, 0]} />)}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : <Empty icon={Clock} title="No study time yet" text="Add courses, then start the timer." to="/courses" cta="Add courses" />}
          </Card>

          <Card delay={0.35}>
            <CardHead title="Coming up" sub="Next 14 days" />
            {data.upcoming.length ? (
              <div className="stack" style={{ gap: 10 }}>
                {data.upcoming.map((e: { id: string; title: string; course: string; date: string; type: string; done: boolean }) => (
                  <motion.div key={e.id} className="row spread" whileHover={{ x: 4 }}
                    style={{ padding: '10px 12px', background: 'var(--bg-base)', borderRadius: 12, border: '1px solid var(--border-subtle)' }}>
                    <div className="grow"><div style={{ fontWeight: 600, textDecoration: e.done ? 'line-through' : 'none' }}>{e.title}</div>
                      <div className="small faint">{e.course} · {niceDate(e.date)}</div></div>
                    <span className={`chip ${e.type}`}>{e.type}</span>
                  </motion.div>
                ))}
              </div>
            ) : <p className="muted">Nothing due in the next two weeks.</p>}
          </Card>
        </div>

        <Card delay={0.4}>
          <CardHead title="Risk snapshot" sub="Decision-tree chance of finishing each course with a D or F">
            <Link to="/risk" className="btn sm" style={{ gap: 6 }}><Sparkles size={14} /> Full risk check</Link>
          </CardHead>
          {data.risk.length ? (
            <div className="grid cols-4">
              {data.risk.map((r: { course: string; probability: number; tier: string }) => {
                const t = tierInfo(r.tier)
                return (
                  <motion.div key={r.course} whileHover={{ y: -4 }} style={{ padding: 16, background: 'var(--bg-base)', borderRadius: 16, border: `1px solid ${t.color}44` }}>
                    <div className="row spread"><b>{r.course}</b><Badge tone={r.tier === 'at_risk' ? 'danger' : r.tier === 'watch' ? 'warning' : ''}>{t.label}</Badge></div>
                    <div className="num" style={{ fontSize: 34, color: t.color, margin: '8px 0 8px' }}>{pct(r.probability)}</div>
                    <div className="progress"><motion.div initial={{ width: 0 }} animate={{ width: pct(r.probability) }} style={{ background: t.color, boxShadow: `0 0 12px ${t.color}` }} transition={{ duration: 1 }} /></div>
                  </motion.div>
                )
              })}
            </div>
          ) : <p className="muted">Add a course to see your risk outlook.</p>}
        </Card>
      </div>
    </>
  )
}
