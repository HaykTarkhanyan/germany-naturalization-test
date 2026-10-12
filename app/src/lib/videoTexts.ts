// Text versions of the explainer videos, parsed from the video scripts (videos/scripts/NN_*.md) at startup, so
// the narration is read from the same file the videos were voiced from. Any format slip throws, like data.ts.
import { QUESTION_BY_ID, TOPIC_BY_KEY } from './data.ts'

const FILES = import.meta.glob('../../../videos/scripts/*.md', { query: '?raw', import: 'default', eager: true }) as Record<string, string>

export const VIDEO_LANGS = ['ru', 'en'] as const
export type VideoLang = (typeof VIDEO_LANGS)[number]

export type Scene = {
  title: string
  /** The term card of the scene (German key terms). */
  screen: string
  /** Narration with {Q123} markers where an exam answer is revealed. */
  voice: Record<VideoLang, string>
  questions: number[]
}
export type VideoText = { slug: string; number: string; title: string; lessons: string[]; scenes: Scene[] }

const MARKER = /\{Q(\d+)\}/g
const markers = (voice: string) => [...voice.matchAll(MARKER)].map((m) => Number(m[1]))
const sorted = (ids: number[]) => [...ids].sort((a, b) => a - b).join()

function parseScript(file: string, src: string): VideoText {
  const fail = (msg: string): never => {
    throw new Error(`videos/scripts/${file}: ${msg}`)
  }
  const head = /^# (\d\d) (.+)$/m.exec(src) ?? fail('no "# NN Title" line')
  const lessonLine = /^Lessons?: (.+)$/m.exec(src) ?? fail('no "Lessons:" line')
  const lessons = [...lessonLine[1].split(' · ')[0].matchAll(/`([a-z_]+)`/g)].map((m) => m[1])
  for (const key of lessons) if (!TOPIC_BY_KEY.has(key)) fail(`unknown lesson ${key}`)
  if (lessons.length === 0) fail('no lesson keys on the "Lessons:" line')
  const scenes = src
    .split('\n## ')
    .slice(1)
    .map((block): Scene => {
      const title = block.split('\n', 1)[0].replace(/\s*\(~[^)]*\)\s*$/, '')
      const field = (name: string) =>
        new RegExp(`^- \\*\\*${name}:\\*\\* (.*)$`, 'm').exec(block)?.[1].trim() ?? fail(`scene "${title}" has no ${name}`)
      const q = field('Questions')
      const questions = q === '-' ? [] : q.split(',').map((s) => Number(s.trim()))
      const voice = { ru: field('Voice RU'), en: field('Voice EN') }
      for (const id of questions) if (!QUESTION_BY_ID.has(id)) fail(`scene "${title}" lists unknown question ${id}`)
      for (const lang of VIDEO_LANGS) {
        if (sorted(markers(voice[lang])) !== sorted(questions)) fail(`scene "${title}": {Q} markers in Voice ${lang.toUpperCase()} differ from Questions`)
      }
      return { title, screen: field('On screen'), voice, questions }
    })
  if (scenes.length === 0) fail('no "## " scenes')
  return { slug: file.replace(/\.md$/, ''), number: head[1], title: head[2], lessons, scenes }
}

export const VIDEO_TEXTS: VideoText[] = Object.entries(FILES)
  .map(([path, src]) => parseScript(path.split('/').pop() ?? path, src))
  .sort((a, b) => a.number.localeCompare(b.number))
export const VIDEO_TEXT_BY_SLUG = new Map(VIDEO_TEXTS.map((v) => [v.slug, v]))

// The series answers every exam question exactly once.
const answered = VIDEO_TEXTS.flatMap((v) => v.scenes.flatMap((s) => s.questions))
const missing = [...QUESTION_BY_ID.keys()].filter((id) => !answered.includes(id))
const twice = answered.filter((id, i) => answered.indexOf(id) !== i)
if (missing.length > 0 || twice.length > 0) {
  throw new Error(`videos/scripts: questions not answered in any video [${missing}], answered twice [${twice}]`)
}

/** The video text that covers a lesson, if any. */
export function videoForLesson(topicKey: string): VideoText | null {
  return VIDEO_TEXTS.find((v) => v.lessons.includes(topicKey)) ?? null
}

/** Narration split into text and the question ids revealed at each {Q} marker. */
export function narrationParts(voice: string): (string | number)[] {
  return voice.split(/\{Q(\d+)\}/).map((part, i) => (i % 2 === 1 ? Number(part) : part))
}

/** Whole minutes at 180 words per minute (as lessons), at least 1. */
export function videoReadingMinutes(v: VideoText, lang: VideoLang): number {
  const words = v.scenes.map((s) => s.voice[lang].replace(MARKER, ' ')).join(' ').split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 180))
}
