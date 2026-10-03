import { createContext, useCallback, useContext, useEffect, useId, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, animate, motion, useInView } from 'framer-motion'
import { CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'
import { api } from '../api'
import type { Json } from '../api'

/* ---------- toasts ---------- */
type Toast = { id: number; text: string; err?: boolean }
const ToastCtx = createContext<(text: string, err?: boolean) => void>(() => {})
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const push = useCallback((text: string, err?: boolean) => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, text, err }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), err ? 6000 : 3500)
  }, [])
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div key={t.id} className={`toast ${t.err ? 'err' : ''}`}
              initial={{ opacity: 0, x: 60, scale: 0.9 }} animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 60 }} transition={{ type: 'spring', stiffness: 380, damping: 28 }}>
              {t.err ? <XCircle size={18} color="var(--danger)" /> : <CheckCircle2 size={18} color="var(--glow)" />}
              {t.text}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  )
}

/* ---------- data hook ---------- */
export const refreshBus = new EventTarget()
export const notifyChange = () => refreshBus.dispatchEvent(new Event('change'))

export function useApi<T = Json>(path: string | null, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const h = () => setTick((t) => t + 1)
    refreshBus.addEventListener('change', h)
    return () => refreshBus.removeEventListener('change', h)
  }, [])
  useEffect(() => {
    if (!path) return
    let live = true
    api.get(path).then((d) => live && (setData(d), setError(null))).catch((e) => live && setError(e.message))
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, tick, ...deps])
  return { data, error, loading: !data && !error, reload: () => setTick((t) => t + 1) }
}

/* ---------- layout bits ---------- */
export function PageHeader({ title, accent, sub, children }: { title: string; accent?: string; sub?: string; children?: ReactNode }) {
  return (
    <motion.div className="page-head" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
      <div>
        <h1>{title} {accent && <span>{accent}</span>}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {children && <div className="row">{children}</div>}
    </motion.div>
  )
}

export function Card({ children, className = '', hover, delay = 0, style }: { children: ReactNode; className?: string; hover?: boolean; delay?: number; style?: React.CSSProperties }) {
  return (
    <motion.div className={`card ${hover ? 'hover' : ''} ${className}`} style={style}
      initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}>
      {children}
    </motion.div>
  )
}

export function CardHead({ title, sub, children }: { title: string; sub?: string; children?: ReactNode }) {
  return (
    <div className="card-head">
      <div><h3>{title}</h3>{sub && <div className="sub">{sub}</div>}</div>
      {children && <div className="row">{children}</div>}
    </div>
  )
}

export function Btn({ children, kind = '', icon: Icon, busy, ...rest }:
  React.ButtonHTMLAttributes<HTMLButtonElement> & { kind?: string; icon?: LucideIcon; busy?: boolean }) {
  return (
    <button className={`btn ${kind} ${rest.className ?? ''}`} {...rest} disabled={rest.disabled || busy}>
      {busy ? <Loader2 size={16} className="spin" /> : Icon && <Icon size={16} />}
      {children}
    </button>
  )
}

export function Badge({ children, tone = '' }: { children: ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <div className="field"><label>{label}</label>{children}</div>
}

export function Segmented<T extends string>({ options, value, onChange }: { options: T[]; value: T; onChange: (v: T) => void }) {
  const id = useId()
  return (
    <div className="seg">
      {options.map((o) => (
        <button key={o} className={o === value ? 'on' : ''} onClick={() => onChange(o)}>
          {o === value && <motion.span layoutId={id} className="thumb" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}
          <span style={{ position: 'relative' }}>{o}</span>
        </button>
      ))}
    </div>
  )
}

export function Empty({ icon: Icon, title, text, to, cta }: { icon: LucideIcon; title: string; text: string; to?: string; cta?: string }) {
  return (
    <div className="empty">
      <div className="em"><Icon size={32} /></div>
      <h3>{title}</h3><p>{text}</p>
      {to && <Link to={to} className="btn primary" style={{ marginTop: 18 }}>{cta ?? 'Go'}</Link>}
    </div>
  )
}

export function Modal({ open, onClose, children }: { open: boolean; onClose: () => void; children: ReactNode }) {
  // Portal to <body>: cards use backdrop-filter, which would otherwise trap position:fixed inside the card.
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div className="modal-bg" onClick={onClose} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <motion.div className="modal" onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.88, y: 30, opacity: 0 }} animate={{ scale: 1, y: 0, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 340, damping: 26 }}>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}

export function Confirm({ open, text, label = 'Confirm', onYes, onClose }: { open: boolean; text: ReactNode; label?: string; onYes: () => void; onClose: () => void }) {
  return (
    <Modal open={open} onClose={onClose}>
      <h3>Are you sure?</h3><p className="muted">{text}</p>
      <div className="row" style={{ marginTop: 22, justifyContent: 'flex-end' }}>
        <Btn onClick={onClose}>Cancel</Btn>
        <Btn kind="danger" onClick={() => { onYes(); onClose() }}>{label}</Btn>
      </div>
    </Modal>
  )
}

/* ---------- animated number ---------- */
export function Counter({ value, decimals = 0, suffix = '' }: { value: number; decimals?: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const [shown, setShown] = useState(0)
  useEffect(() => {
    if (!inView) return
    const c = animate(0, value, { duration: 1.1, ease: [0.22, 1, 0.36, 1], onUpdate: setShown })
    return () => c.stop()
  }, [value, inView])
  return <span ref={ref}>{shown.toFixed(decimals)}{suffix}</span>
}

export function Stat({ label, value, decimals = 0, unit, icon: Icon, delay = 0 }:
  { label: string; value: number; decimals?: number; unit?: string; icon: LucideIcon; delay?: number }) {
  return (
    <Card className="stat" hover delay={delay}>
      <Icon className="ico" size={28} />
      <div className="caps">{label}</div>
      <div className="v"><Counter value={value} decimals={decimals} />{unit && <small>{unit}</small>}</div>
    </Card>
  )
}

export function Progress({ value }: { value: number }) {
  return (
    <div className="progress">
      <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(100, value * 100)}%` }} transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }} />
    </div>
  )
}

export function Skeleton({ h = 120 }: { h?: number }) { return <div className="skeleton" style={{ height: h }} /> }

export function Loading() {
  return <div className="grid cols-3"><Skeleton h={140} /><Skeleton h={140} /><Skeleton h={140} /></div>
}

export function Md({ text }: { text: string }) {
  // Tiny markdown renderer: ### headings, - bullets, **bold**
  const inline = (s: string): ReactNode[] =>
    s.split(/(\*\*[^*]+\*\*)/g).map((p, i) => (p.startsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong> : p))
  const out: ReactNode[] = []
  let list: string[] = []
  const flush = () => { if (list.length) { out.push(<ul key={out.length}>{list.map((l, i) => <li key={i}>{inline(l)}</li>)}</ul>); list = [] } }
  text.split('\n').forEach((line) => {
    const t = line.trim()
    if (/^#{1,4}\s/.test(t)) { flush(); out.push(<h3 key={out.length}>{t.replace(/^#+\s/, '')}</h3>) }
    else if (/^[-*•]\s/.test(t)) list.push(t.slice(2))
    else if (t) { flush(); out.push(<p key={out.length}>{inline(t)}</p>) }
  })
  flush()
  return <div className="md">{out}</div>
}

export function FilePick({ onFiles, accept, multiple, label }: { onFiles: (f: File[]) => void; accept: string; multiple?: boolean; label: string }) {
  const [over, setOver] = useState(false)
  const id = useId()
  return (
    <label htmlFor={id} className={`drop ${over ? 'over' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); onFiles(Array.from(e.dataTransfer.files)) }}>
      <input id={id} type="file" accept={accept} multiple={multiple} onChange={(e) => e.target.files && onFiles(Array.from(e.target.files))} />
      {label}
    </label>
  )
}

export const COLORS = ['#4cf04c', '#2db32d', '#4cc9f0', '#ffb020', '#c9a3ff', '#ff5c6c', '#7dff7d', '#b3b9b0']
export const courseColor = (courses: string[], c: string) => COLORS[Math.max(0, courses.indexOf(c)) % COLORS.length]
