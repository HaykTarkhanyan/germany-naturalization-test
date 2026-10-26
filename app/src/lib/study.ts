// The readable per-topic files in study/ (scripts/build_study_files.py), copied into the site by vite.config.ts.
import { TOPICS } from './data.ts'
import type { Lang } from './settings.ts'

/** study/<lang>/<NN>_<topic>.<ext>, NN = the topic's position in data/topics.json (01-24). */
export function studyFile(topicKey: string, lang: Lang, ext: 'html' | 'pdf'): string {
  const i = TOPICS.findIndex((t) => t.key === topicKey)
  if (i < 0) throw new Error(`no topic ${topicKey}`)
  return `${import.meta.env.BASE_URL}study/${lang}/${String(i + 1).padStart(2, '0')}_${topicKey}.${ext}`
}

export function studyIndex(): string {
  return `${import.meta.env.BASE_URL}study/index.html`
}
