import { motion } from 'framer-motion'
import { Card, CardHead, Loading, PageHeader, Progress, useApi } from '../components/ui'

type B = { key: string; category: string; icon: string; name: string; desc: string; unlocked: boolean; progress: number; value: number; goal: number }

export default function Achievements() {
  const { data } = useApi('/achievements')
  if (!data) return <Loading />
  const badges: B[] = data.badges
  const got = badges.filter((b) => b.unlocked).length
  return (
    <>
      <PageHeader title="Achieve" accent="ments" sub="Badges for streaks, study hours, quiz scores and keeping on top of deadlines." />
      <Card style={{ marginBottom: 20 }}>
        <div className="row spread"><div><div className="caps">Unlocked</div><div className="num" style={{ fontSize: 44, color: 'var(--glow)' }}>{got}<span className="muted" style={{ fontSize: 22 }}> / {badges.length}</span></div></div>
          <div style={{ width: 'min(480px, 100%)' }}><Progress value={got / badges.length} /></div></div>
      </Card>
      {data.categories.map((cat: string, ci: number) => (
        <Card key={cat} delay={ci * 0.05} style={{ marginBottom: 20 }}>
          <CardHead title={cat} sub={`${badges.filter((b) => b.category === cat && b.unlocked).length} of ${badges.filter((b) => b.category === cat).length}`} />
          <div className="grid cols-3">
            {badges.filter((b) => b.category === cat).map((b, i) => (
              <motion.div key={b.key} className={`ach ${b.unlocked ? 'on' : ''}`} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
                <div className="ic">{b.icon}</div>
                <div className="grow"><div style={{ fontWeight: 700 }}>{b.name}</div><div className="small muted">{b.desc}</div>
                  {!b.unlocked && <div style={{ marginTop: 8 }}><Progress value={b.progress} /><div className="small faint" style={{ marginTop: 4 }}>{Math.min(b.value, b.goal).toFixed(b.goal < 10 ? 1 : 0).replace(/\.0$/, '')} / {b.goal}</div></div>}
                </div>
              </motion.div>
            ))}
          </div>
        </Card>
      ))}
    </>
  )
}
