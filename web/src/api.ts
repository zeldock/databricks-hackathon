// Thin client for the Wolf Tracks API (see ../api.py).
/* eslint-disable @typescript-eslint/no-explicit-any */
export type Json = any

async function call(method: string, path: string, body?: unknown): Promise<Json> {
  const isForm = body instanceof FormData
  const res = await fetch(`/api${path}`, {
    method,
    headers: body && !isForm ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? (isForm ? (body as FormData) : JSON.stringify(body)) : undefined,
  })
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail ?? detail } catch { /* not json */ }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.json()
}

export const api = {
  get: (p: string) => call('GET', p),
  post: (p: string, b?: unknown) => call('POST', p, b ?? {}),
  put: (p: string, b?: unknown) => call('PUT', p, b ?? {}),
  patch: (p: string, b?: unknown) => call('PATCH', p, b ?? {}),
  del: (p: string) => call('DELETE', p),
  form: (p: string, f: FormData) => call('POST', p, f),
}

export const fmtHours = (h: number) => (h >= 10 ? h.toFixed(0) : h.toFixed(1))
export const pct = (v: number, d = 0) => `${(v * 100).toFixed(d)}%`
export const iso = (d: Date) => {
  const z = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`
}
export const parseISO = (s: string) => {
  const [y, m, d] = s.slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d)
}
export const niceDate = (s: string) =>
  parseISO(s).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
