import { defineConfig } from 'vite'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))

/** Lists the hand-drawn wolf images in public/wolf (png/webp/svg) so the app can use whatever is there. */
function wolfManifest(): Plugin {
  const dir = path.resolve(here, 'public/wolf')
  const build = () => {
    const files: Record<string, string> = {}
    if (fs.existsSync(dir)) {
      for (const f of fs.readdirSync(dir)) {
        const m = /^(.+)\.(png|webp|svg)$/i.exec(f)
        if (m) files[m[1]] = `${f}?v=${Math.floor(fs.statSync(path.join(dir, f)).mtimeMs)}`
      }
    }
    return JSON.stringify({ files })
  }
  return {
    name: 'wolf-manifest',
    configureServer(server) {
      server.middlewares.use('/wolf/manifest.json', (_req, res) => {
        res.setHeader('Content-Type', 'application/json')
        res.setHeader('Cache-Control', 'no-store')
        res.end(build())
      })
    },
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: 'wolf/manifest.json', source: build() })
    },
  }
}

export default defineConfig({
  plugins: [react(), wolfManifest()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
})
