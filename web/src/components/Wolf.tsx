import { useId } from 'react'
import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { FUR_FILTER, useWolfAssets } from '../wolfAssets'

export type Mood = 'ecstatic' | 'happy' | 'content' | 'worried' | 'sad'
export type Equipped = Partial<Record<'hat' | 'eyewear' | 'neck' | 'back' | 'fur' | 'scene', string | null>>

const FUR: Record<string, { base: string; light: string; dark: string; inner: string }> = {
  fur_gray: { base: '#8b949e', light: '#d9dfe5', dark: '#5b636b', inner: '#c98b95' },
  fur_snow: { base: '#e6edf2', light: '#ffffff', dark: '#aab6c0', inner: '#f2b8c0' },
  fur_midnight: { base: '#3d4c6e', light: '#7184ae', dark: '#232c46', inner: '#8a6f9e' },
  fur_ember: { base: '#b8683c', light: '#f2cfa6', dark: '#7a4022', inner: '#e59a8a' },
  fur_emerald: { base: '#2db32d', light: '#bff7bf', dark: '#157a22', inner: '#7fe39a' },
  fur_golden: { base: '#e2ab2a', light: '#fff1b8', dark: '#a8760f', inner: '#f5a97f' },
}

/* ---------------------------------------------------------------- scenes */
function Scene({ id }: { id: string }) {
  const g = useId()
  const stars = [[40, 50], [90, 120], [150, 40], [330, 70], [360, 150], [60, 200], [310, 30], [250, 90], [20, 120]]
  const Stars = ({ o = 0.8 }: { o?: number }) => (
    <>{stars.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={i % 3 ? 1.6 : 2.4} fill="#fff" opacity={o} />)}</>
  )
  switch (id) {
    case 'scene_moon':
      return (<g>
        <defs><linearGradient id={g} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#0b1a33" /><stop offset="1" stopColor="#0f3a2a" /></linearGradient></defs>
        <rect width="400" height="420" fill={`url(#${g})`} /><Stars />
        <circle cx="300" cy="95" r="52" fill="#f4f1d0" /><circle cx="285" cy="82" r="10" fill="#e3dfb4" /><circle cx="318" cy="108" r="7" fill="#e3dfb4" />
        <path d="M0 360 Q120 320 220 350 T400 340 V420 H0Z" fill="#0b2a1c" /></g>)
    case 'scene_forest':
      return (<g>
        <defs><linearGradient id={g} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#0a2418" /><stop offset="1" stopColor="#12462b" /></linearGradient></defs>
        <rect width="400" height="420" fill={`url(#${g})`} /><circle cx="330" cy="70" r="26" fill="#e8f5d0" opacity=".85" />
        {[[30, 330, 70], [90, 350, 90], [320, 340, 80], [370, 360, 95], [270, 360, 60]].map(([x, y, h], i) => (
          <g key={i}><path d={`M${x} ${y - h} L${x - h / 3} ${y} L${x + h / 3} ${y}Z`} fill="#0a2f1d" /><path d={`M${x} ${y - h * 0.65} L${x - h / 2.6} ${y - h * 0.15} L${x + h / 2.6} ${y - h * 0.15}Z`} fill="#0d3a23" /></g>))}
        <rect y="370" width="400" height="50" fill="#0a2012" /></g>)
    case 'scene_library':
      return (<g>
        <rect width="400" height="420" fill="#17140f" />
        {[40, 140, 240].map((y, r) => (<g key={y}><rect x="0" y={y + 62} width="400" height="8" fill="#3a2a16" />
          {Array.from({ length: 16 }).map((_, i) => <rect key={i} x={10 + i * 24} y={y + 62 - (28 + ((i * 7 + r * 3) % 4) * 6)} width="18" height={28 + ((i * 7 + r * 3) % 4) * 6} rx="2" fill={['#2d6b3a', '#7a2f2f', '#2f4a7a', '#8a6a2a', '#4a2f7a'][(i + r) % 5]} />)}</g>))}
        <rect width="400" height="420" fill="#000" opacity=".25" /></g>)
    case 'scene_aurora':
      return (<g>
        <defs><linearGradient id={g} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#04101a" /><stop offset="1" stopColor="#09201a" /></linearGradient>
          <linearGradient id={g + 'a'} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#4cf04c" stopOpacity="0" /><stop offset=".5" stopColor="#4cf04c" stopOpacity=".6" /><stop offset="1" stopColor="#4cc9f0" stopOpacity="0" /></linearGradient></defs>
        <rect width="400" height="420" fill={`url(#${g})`} /><Stars o={0.6} />
        <motion.path d="M-20 130 Q80 40 180 120 T380 90 V230 Q300 170 200 220 T-20 210Z" fill={`url(#${g}a)`} animate={{ x: [0, 20, 0], opacity: [0.7, 1, 0.7] }} transition={{ duration: 7, repeat: Infinity }} />
        <motion.path d="M-20 190 Q100 120 220 180 T420 150 V260 Q300 230 200 270 T-20 260Z" fill="#c9a3ff" opacity=".18" animate={{ x: [0, -24, 0] }} transition={{ duration: 9, repeat: Infinity }} /></g>)
    case 'scene_space':
      return (<g>
        <rect width="400" height="420" fill="#04040c" /><Stars /><Stars o={0.5} />
        <circle cx="80" cy="90" r="34" fill="#2db32d" /><ellipse cx="80" cy="90" rx="58" ry="10" fill="none" stroke="#b3b9b0" strokeWidth="3" opacity=".8" transform="rotate(-20 80 90)" />
        <circle cx="330" cy="330" r="20" fill="#4cc9f0" opacity=".8" /></g>)
    default:
      return (<g>
        <defs><radialGradient id={g} cx=".5" cy=".42" r=".7"><stop offset="0" stopColor="#1d4a24" /><stop offset=".6" stopColor="#0d1f10" /><stop offset="1" stopColor="#060906" /></radialGradient></defs>
        <rect width="400" height="420" fill={`url(#${g})`} /></g>)
  }
}

/* ----------------------------------------------------------- accessories */
// Hats, eyewear and neckwear are hand-drawn images (public/wolf/hat-<id>.png ...). The Golden Halo is the one vector item.
const Halo = () => (
  <g><ellipse cx="200" cy="60" rx="56" ry="13" fill="none" stroke="#ffe27a" strokeWidth="9" /><ellipse cx="200" cy="60" rx="56" ry="13" fill="none" stroke="#fff" strokeWidth="2" opacity=".7" /></g>
)

/* ------------------------------------------------------------------ face */
function Eye({ cx, mood }: { cx: number; mood: Mood }) {
  const cy = 172
  if (mood === 'ecstatic') return <path d={`M${cx - 18} ${cy + 8} Q${cx} ${cy - 18} ${cx + 18} ${cy + 8}`} stroke="#141a15" strokeWidth="7" fill="none" strokeLinecap="round" />
  return (
    <g className="wolf-blink">
      <ellipse cx={cx} cy={cy} rx="18" ry="20" fill="#f6fbf6" />
      <circle cx={cx + (mood === 'sad' ? 0 : 1)} cy={cy + (mood === 'sad' || mood === 'worried' ? 4 : 1)} r="12" fill="#35cf54" />
      <circle cx={cx} cy={cy + (mood === 'sad' || mood === 'worried' ? 4 : 1)} r="7" fill="#08130a" />
      <circle cx={cx - 4} cy={cy - 5} r="4.2" fill="#fff" />
      <circle cx={cx + 5} cy={cy + 5} r="2" fill="#fff" opacity=".8" />
    </g>
  )
}

function Face({ mood, fur }: { mood: Mood; fur: (typeof FUR)[string] }) {
  const dark = '#141a15'
  const mouth: ReactNode = {
    ecstatic: (<g><path d="M168 236 Q200 292 232 236 Q200 248 168 236Z" fill="#3a0f14" /><ellipse cx="200" cy="266" rx="15" ry="11" fill="#ff7f93" /></g>),
    happy: (<g><path d="M200 226 V240" stroke={dark} strokeWidth="5" strokeLinecap="round" /><path d="M170 238 Q200 270 230 238" stroke={dark} strokeWidth="5.5" fill="none" strokeLinecap="round" /><ellipse cx="206" cy="262" rx="11" ry="8" fill="#ff7f93" /></g>),
    content: (<g><path d="M200 226 V238" stroke={dark} strokeWidth="5" strokeLinecap="round" /><path d="M178 240 Q200 254 222 240" stroke={dark} strokeWidth="5.5" fill="none" strokeLinecap="round" /></g>),
    worried: (<g><path d="M200 226 V238" stroke={dark} strokeWidth="5" strokeLinecap="round" /><path d="M178 250 Q189 240 200 246 Q211 252 222 242" stroke={dark} strokeWidth="5.5" fill="none" strokeLinecap="round" /></g>),
    sad: (<g><path d="M200 226 V240" stroke={dark} strokeWidth="5" strokeLinecap="round" /><path d="M176 256 Q200 230 224 256" stroke={dark} strokeWidth="5.5" fill="none" strokeLinecap="round" /></g>),
  }[mood]
  return (
    <g>
      <ellipse cx="200" cy="224" rx="56" ry="42" fill={fur.light} />
      <path d="M184 205 Q200 195 216 205 Q214 224 200 228 Q186 224 184 205Z" fill="#161b17" /><ellipse cx="195" cy="205" rx="6" ry="3" fill="#fff" opacity=".35" />
      {mouth}
      {(mood === 'happy' || mood === 'ecstatic') && <><ellipse cx="124" cy="214" rx="17" ry="10" fill="#ff8fa3" opacity=".5" /><ellipse cx="276" cy="214" rx="17" ry="10" fill="#ff8fa3" opacity=".5" /></>}
      <Eye cx={155} mood={mood} /><Eye cx={245} mood={mood} />
      {mood === 'sad' && (<>
        <path d="M134 150 L178 136" stroke={fur.dark} strokeWidth="7" strokeLinecap="round" /><path d="M266 150 L222 136" stroke={fur.dark} strokeWidth="7" strokeLinecap="round" />
        <path d="M133 160 Q160 142 180 160 L180 150 Q160 128 133 146Z" fill={fur.base} /><path d="M267 160 Q240 142 220 160 L220 150 Q240 128 267 146Z" fill={fur.base} />
        <motion.path d="M142 196 q-7 14 0 22 q8 -8 0 -22z" fill="#6fd6ff" animate={{ y: [0, 34], opacity: [1, 0] }} transition={{ duration: 1.8, repeat: Infinity, ease: 'easeIn' }} /></>)}
      {mood === 'worried' && (<>
        <path d="M132 152 L174 138" stroke={fur.dark} strokeWidth="7" strokeLinecap="round" /><path d="M268 152 L226 138" stroke={fur.dark} strokeWidth="7" strokeLinecap="round" />
        <motion.path d="M262 134 q-7 13 0 20 q8 -7 0 -20z" fill="#6fd6ff" animate={{ y: [0, 6, 0] }} transition={{ duration: 1.4, repeat: Infinity }} /></>)}
    </g>
  )
}

/* ------------------------------------------------------------------ wolf */
/** Where the square hand-drawn canvas sits in the 400x420 drawing space (tune if the art looks offset). */
const ART = { s: 430, x: -15, y: -17 }

export default function Wolf({ mood = 'content', equipped = {}, size = 320, crop = 'full', scene = true, pat = 0, animate = true, tint: tintOverride }:
  { mood?: Mood; equipped?: Equipped; size?: number; crop?: 'full' | 'head'; scene?: boolean; pat?: number; animate?: boolean; tint?: string }) {
  const A = useWolfAssets()
  const furKey = equipped.fur ?? 'fur_gray'
  const fur = FUR[furKey] ?? FUR.fur_gray
  // Hand-drawn art (see docs/WOLF_ART_GUIDE.md): one full-wolf image per mood on a square canvas, a separate tail,
  // and accessory layers on the same canvas. A mood falls back to its nearest drawn neighbour.
  const NEAR: Record<Mood, Mood[]> = { ecstatic: ['happy', 'content'], happy: ['ecstatic', 'content'], content: ['happy', 'sad'], worried: ['sad', 'content'], sad: ['worried', 'content'] }
  const wolfKey = [mood, ...NEAR[mood]].map((m) => `wolf-${m}`).find((k) => A[`${k}-${furKey}`] || A[k])
  const wolfImg = wolfKey ? (A[`${wolfKey}-${furKey}`] ?? A[wolfKey]) : null
  const tailImg = A[`tail-${furKey}`] ?? A.tail ?? null
  const art = !!wolfImg
  const tint = tintOverride ?? (wolfKey && A[`${wolfKey}-${furKey}`] ? undefined : FUR_FILTER[furKey])
  const Pic = ({ url, filter }: { url: string; filter?: string }) => <image href={url} x={ART.x} y={ART.y} width={ART.s} height={ART.s} preserveAspectRatio="xMidYMid meet" style={filter ? { filter } : undefined} />
  const withArt = (key: string, fallback: React.ReactNode = null) => (A[key] ? <Pic url={A[key]} /> : fallback)
  const droop = mood === 'sad' ? 24 : mood === 'worried' ? 12 : 0
  const wag = animate && (mood === 'happy' || mood === 'ecstatic')
  const viewBox = crop === 'head' ? '50 -50 300 330' : '0 0 400 420'
  const height = crop === 'head' ? (size * 330) / 300 : (size * 420) / 400
  const Ear = ({ d }: { d: number }) => (
    <g transform={`rotate(${-d} 150 118)`}>
      <path d="M108 134 L116 22 L184 94Z" fill={fur.base} stroke={fur.dark} strokeWidth="3" strokeLinejoin="round" />
      <path d="M122 114 L124 54 L162 92Z" fill={fur.inner} />
    </g>
  )
  const Cheek = () => <path d="M108 176 L64 204 L98 212 L68 244 L128 236Z" fill={fur.base} stroke={fur.dark} strokeWidth="3" strokeLinejoin="round" />
  return (
    <svg viewBox={viewBox} width={size} height={height} style={{ display: 'block', maxWidth: '100%', height: 'auto', overflow: crop === 'head' ? 'hidden' : 'visible', borderRadius: scene ? 28 : 0 }} role="img" aria-label={`A ${mood} wolf`}>
      <style>{`.wolf-blink{transform-box:fill-box;transform-origin:center;animation:wolfblink 5s infinite}@keyframes wolfblink{0%,94%,100%{transform:scaleY(1)}97%{transform:scaleY(.08)}}`}</style>
      {scene && (A[`scene-${equipped.scene ?? 'scene_den'}`] ? <image href={A[`scene-${equipped.scene ?? 'scene_den'}`]} x="0" y="0" width="400" height="420" preserveAspectRatio="xMidYMid slice" /> : <Scene id={equipped.scene ?? 'scene_den'} />)}
      <ellipse cx="200" cy="410" rx="120" ry="12" fill="#000" opacity=".35" />
      <motion.g className="pv" style={art ? { originX: '237px', originY: '314px' } : { originX: '290px', originY: '350px' }} animate={animate ? { rotate: wag ? [-14, 16, -14] : mood === 'sad' ? 8 : [0, 3, 0] } : undefined} transition={{ duration: wag ? (mood === 'ecstatic' ? 0.45 : 0.8) : 4, repeat: Infinity, ease: 'easeInOut' }}>
        {art ? (tailImg && <Pic url={tailImg} filter={tint} />) : (<>
        <path d={mood === 'sad' ? 'M288 372 C340 380 352 400 340 412 C320 404 300 398 276 392Z' : 'M288 372 C352 360 380 292 350 240 C346 290 316 320 276 332Z'} fill={fur.base} stroke={fur.dark} strokeWidth="3" strokeLinejoin="round" />
        <path d={mood === 'sad' ? 'M340 412 C332 408 326 404 322 400Z' : 'M350 240 C360 262 358 280 350 296 C360 280 362 258 350 240Z'} fill={fur.light} />
        </>)}
      </motion.g>
      <motion.g className="pv" style={{ originX: '200px', originY: '420px' }} animate={animate ? { scaleY: [1, 1.012, 1] } : undefined} transition={{ duration: 3.4, repeat: Infinity, ease: 'easeInOut' }}>
        {art ? null : (<>
        <path d="M104 418 C98 336 140 286 200 286 C260 286 302 336 296 418Z" fill={fur.base} stroke={fur.dark} strokeWidth="3" />
        <ellipse cx="200" cy="352" rx="46" ry="62" fill={fur.light} />
        <ellipse cx="156" cy="410" rx="32" ry="12" fill={fur.light} stroke={fur.dark} strokeWidth="2" /><ellipse cx="244" cy="410" rx="32" ry="12" fill={fur.light} stroke={fur.dark} strokeWidth="2" />
        </>)}
      </motion.g>
      {!art && equipped.neck && withArt(`neck-${equipped.neck}`)}
      <motion.g key={pat} className="pv" style={{ originX: '200px', originY: '280px' }} animate={animate ? (pat ? { rotate: [0, -7, 7, -4, 0], y: [0, -6, 0] } : { y: [0, -3, 0] }) : undefined} transition={pat ? { duration: 0.6 } : { duration: 3.4, repeat: Infinity, ease: 'easeInOut' }}>
        {art ? (<><Pic url={wolfImg!} filter={tint} />{equipped.neck && withArt(`neck-${equipped.neck}`)}</>) : (<>
        <g><Ear d={-droop} /></g><g transform="translate(400 0) scale(-1 1)"><Ear d={-droop} /></g>
        <Cheek /><g transform="translate(400 0) scale(-1 1)"><Cheek /></g>
        <ellipse cx="200" cy="185" rx="100" ry="88" fill={fur.base} stroke={fur.dark} strokeWidth="3" />
        <path d="M200 100 L184 142 L216 142Z" fill={fur.dark} opacity=".55" />
        <Face mood={mood} fur={fur} />
        </>)}
        {equipped.eyewear && withArt(`eyewear-${equipped.eyewear}`)}
        {equipped.hat && withArt(`hat-${equipped.hat}`, equipped.hat === 'halo' ? <Halo /> : null)}
      </motion.g>
      {mood === 'ecstatic' && animate && [[88, 70], [322, 96], [346, 180]].map(([x, y], i) => (
        <motion.path key={i} className="pv" d={`M${x} ${y - 12} l4 9 9 1 -7 6 2 9 -8 -5 -8 5 2 -9 -7 -6 9 -1z`} fill="#ffe27a" animate={{ scale: [0.4, 1.15, 0.4], opacity: [0.2, 1, 0.2] }} transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.4 }} style={{ originX: `${x}px`, originY: `${y}px` }} />))}
    </svg>
  )
}
