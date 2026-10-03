import { useMemo } from 'react'
import Wolf from './Wolf'
import type { Equipped } from './Wolf'

/* A crew of wolves dancing (celebrations and the game menu), plus floating party stickers. */
// Every dancer gets a random outfit from the hand-drawn accessories (hat, eyewear and neckwear, each optional).
const HATS = ['party', 'crown', 'wizard', 'gradcap', 'halo', 'fedora', 'propeller', 'cap_black', 'cap_blue', 'cap_pink', 'cap_yellow']
const EYES: (string | null)[] = [null, null, 'glasses', 'square', 'shades', 'monocle']
const NECKS: (string | null)[] = [null, 'bandana_black', 'bandana_blue', 'bandana_pink', 'bandana_yellow', 'bowtie_black', 'bowtie_blue', 'bowtie_pink', 'bowtie_yellow', 'chain']
const pick = <T,>(xs: T[]) => xs[Math.floor(Math.random() * xs.length)]
// Dancing wolves recolour the hand-drawn grey wolf with a CSS tint (sepia first, so the grey picks up the hue).
const CREW_TINTS = [undefined, 'sepia(1) saturate(3.4) hue-rotate(-35deg)', 'sepia(1) saturate(3.2) hue-rotate(20deg) brightness(1.1)', 'sepia(1) saturate(3) hue-rotate(75deg)', 'sepia(1) saturate(3) hue-rotate(140deg)', 'sepia(1) saturate(3.2) hue-rotate(185deg)', 'sepia(1) saturate(3) hue-rotate(235deg) brightness(.95)', 'sepia(1) saturate(3.4) hue-rotate(285deg)', 'sepia(1) saturate(3.4) hue-rotate(325deg)', 'brightness(1.5) saturate(.4)', 'brightness(.55) contrast(1.1)']
const DANCES = ['dance-bounce', 'dance-sway', 'dance-spin', 'dance-hop', 'dance-wiggle']

/** A row of dancing wolves. They are static art animated with CSS, so a big crew stays cheap. */
export function DancingCrew({ wolves = 8, size = 120, seed = 1, className = '' }: { wolves?: number; size?: number; seed?: number; className?: string }) {
  const crew = useMemo(() => Array.from({ length: wolves }, (_, k) => ({
    k, dance: DANCES[(k + seed) % DANCES.length], delay: (k * 0.17) % 0.9, dur: 0.55 + ((k * 0.13) % 0.4), big: 0.85 + ((k * 0.11) % 0.35),
    tint: CREW_TINTS[(k * 5 + seed) % CREW_TINTS.length],
    eq: { hat: Math.random() < 0.85 ? pick(HATS) : null, eyewear: pick(EYES), neck: pick(NECKS) } as Equipped,
  })), [wolves, seed])
  return (
    <div className={`crew ${className}`}>
      {crew.map((c) => (
        <div key={c.k} className={`dancer ${c.dance}`} style={{ animationDelay: `${c.delay}s`, animationDuration: `${c.dur}s` }}>
          <Wolf mood="ecstatic" equipped={c.eq} tint={c.tint} size={size * c.big} scene={false} animate={false} />
        </div>
      ))}
    </div>
  )
}

const STICKERS = ['🎉', '🎈', '🍓', '🍰', '🎀', '✨', '💖', '⭐', '🐾', '🪙', '💎', '🎁', '🍩', '🎊', '🌈', '🍭']
export function StickerFloat({ count = 30, spanSec = 8 }: { count?: number; spanSec?: number }) {
  const items = useMemo(() => Array.from({ length: count }, (_, i) => ({
    i, e: STICKERS[i % STICKERS.length], left: Math.random() * 100, size: 28 + Math.random() * 36, delay: Math.random() * spanSec, dur: 4 + Math.random() * 4, sway: (Math.random() - 0.5) * 140,
  })), [count, spanSec])
  return <>{items.map((s) => <span key={s.i} className="sticker" style={{ left: `${s.left}%`, fontSize: s.size, animationDelay: `${s.delay}s`, animationDuration: `${s.dur}s`, ['--sway' as string]: `${s.sway}px` }}>{s.e}</span>)}</>
}
