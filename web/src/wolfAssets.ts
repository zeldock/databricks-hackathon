// Hand-drawn wolf art: whatever images exist in public/wolf are picked up automatically (see docs/WOLF_ART_GUIDE.md).
// Anything missing falls back to the built-in vector wolf, so the app always renders.
import { useEffect, useState } from 'react'

export type WolfAssets = Record<string, string>
let cache: WolfAssets | null = null
let inflight: Promise<WolfAssets> | null = null

export function loadWolfAssets(): Promise<WolfAssets> {
  if (cache) return Promise.resolve(cache)
  inflight ||= fetch('/wolf/manifest.json', { cache: 'no-store' })
    .then((r) => (r.ok ? r.json() : { files: {} }))
    .then((j) => {
      const files: WolfAssets = {}
      for (const [k, v] of Object.entries((j.files ?? {}) as Record<string, string>)) files[k] = `/wolf/${v}`
      cache = files
      Object.values(files).forEach((u) => { const i = new Image(); i.src = u }) // warm the cache
      return files
    })
    .catch(() => (cache = {}))
  return inflight
}

export function useWolfAssets(): WolfAssets {
  const [assets, setAssets] = useState<WolfAssets>(cache ?? {})
  useEffect(() => {
    let live = true
    loadWolfAssets().then((a) => live && setAssets(a))
    return () => { live = false }
  }, [])
  return assets
}

/** Stand-in tints so one hand-drawn grey wolf still gives every fur colour in the shop. Draw per-fur images to replace them. */
export const FUR_FILTER: Record<string, string> = {
  fur_snow: 'brightness(1.5) saturate(0.35) contrast(0.92)',
  fur_midnight: 'sepia(1) hue-rotate(185deg) saturate(1.5) brightness(0.55)',
  fur_ember: 'sepia(1) hue-rotate(-18deg) saturate(2.4) brightness(0.8)',
  fur_emerald: 'sepia(1) hue-rotate(78deg) saturate(2.6) brightness(0.95)',
  fur_golden: 'sepia(1) hue-rotate(5deg) saturate(3.2) brightness(1.15)',
}
