/// <reference types="vitest/config" />
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const appDir = path.dirname(fileURLToPath(import.meta.url))
// The questions, topics and images live in ../data (built by scripts/build_dataset.py), outside the Vite root.
const dataDir = path.resolve(appDir, '..', 'data')
// The video texts are read from the video scripts (src/lib/videoTexts.ts).
const scriptsDir = path.resolve(appDir, '..', 'videos', 'scripts')

export default defineConfig(({ command, isPreview }) => ({
  // GitHub Pages serves the site at /germany-naturalization-test/; the dev server serves it at /.
  base: command === 'serve' && !isPreview ? '/' : '/germany-naturalization-test/',
  plugins: [react()],
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
