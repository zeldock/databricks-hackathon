// "Mega Jackpot Mode" demo toggle: when on, the server makes every slot spin and roulette spin a top prize.
import { useSyncExternalStore } from 'react'

const KEY = 'wolf-tracks-mega'
let on = (() => { try { return localStorage.getItem(KEY) === '1' } catch { return false } })()
const subs = new Set<() => void>()

export const isMega = () => on
export const setMega = (v: boolean) => {
  on = v
  try { localStorage.setItem(KEY, v ? '1' : '0') } catch { /* private mode */ }
  subs.forEach((f) => f())
}
export const useMega = () => useSyncExternalStore((f) => { subs.add(f); return () => subs.delete(f) }, isMega)
