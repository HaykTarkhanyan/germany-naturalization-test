/// <reference types="vitest/config" />
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

const appDir = path.dirname(fileURLToPath(import.meta.url))
// The questions, topics and images live in ../data (built by scripts/build_dataset.py), outside the Vite root.
const dataDir = path.resolve(appDir, '..', 'data')
// The video texts are read from the video scripts (src/lib/videoTexts.ts).
const scriptsDir = path.resolve(appDir, '..', 'videos', 'scripts')
const mp4Dir = path.resolve(appDir, '..', 'videos', 'mp4')

/** The explainer videos (videos/mp4/) on the site at <base>videos/: streamed from disk by the dev server, copied
 * into the build (DECISIONS.md #23). Fails if a script has no rendered video in both languages, so a video page
 * never points at a missing file. */
function explainerVideos(): Plugin {
  const files = (): string[] => {
    const slugs = fs.readdirSync(scriptsDir).filter((f) => f.endsWith('.md')).map((f) => f.slice(0, -3))
    const names = slugs.flatMap((s) => [`${s}.ru.mp4`, `${s}.en.mp4`])
    const missing = names.filter((f) => !fs.existsSync(path.join(mp4Dir, f)))
    if (missing.length > 0) throw new Error(`videos/mp4 has no ${missing.join(', ')}: render them with videos/pipeline/render.py`)
    return names
  }
  return {
    name: 'explainer-videos',
    configureServer(server) {
      const known = new Set(files())
      server.middlewares.use('/videos', (req, res, next) => {
        const name = decodeURIComponent((req.url ?? '').split('?')[0].replace(/^\//, ''))
        if (!known.has(name)) return next()
        const file = path.join(mp4Dir, name)
        const size = fs.statSync(file).size
        const range = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range ?? '') // seeking asks for byte ranges
        res.setHeader('Content-Type', 'video/mp4')
        res.setHeader('Accept-Ranges', 'bytes')
        const start = range ? Number(range[1]) : 0
        const end = range?.[2] ? Number(range[2]) : size - 1
        if (range) {
          res.statusCode = 206
          res.setHeader('Content-Range', `bytes ${start}-${end}/${size}`)
        }
        res.setHeader('Content-Length', end - start + 1)
        fs.createReadStream(file, { start, end }).pipe(res)
      })
    },
    writeBundle(options) {
      const out = path.join(options.dir ?? path.join(appDir, 'dist'), 'videos')
      fs.mkdirSync(out, { recursive: true })
      for (const f of files()) fs.copyFileSync(path.join(mp4Dir, f), path.join(out, f))
    },
  }
}

export default defineConfig(({ command, isPreview }) => ({
  // GitHub Pages serves the site at /germany-naturalization-test/; the dev server serves it at /.
  base: command === 'serve' && !isPreview ? '/' : '/germany-naturalization-test/',
  plugins: [react(), explainerVideos()],
  server: {
    port: 5174,
    strictPort: true,
    fs: { allow: [appDir, dataDir, scriptsDir] },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
}))
