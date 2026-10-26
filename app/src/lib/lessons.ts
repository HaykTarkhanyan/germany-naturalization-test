// Study lessons (data/lessons.json): one short read per topic, validated at startup like data.ts.
// Every lesson must cover exactly the questions of its topic, so no exam question is left unread.
// data/lessons_ru.json holds the same lessons in Russian (text only; question numbers come from lessons.json).
import { z } from 'zod'
import lessonsJson from '../../../data/lessons.json' with { type: 'json' }
import lessonsRuJson from '../../../data/lessons_ru.json' with { type: 'json' }
import { parse, QUESTION_BY_ID, TOPIC_BY_KEY, TOPICS } from './data.ts'
import { EXAM } from './exam.ts'
import type { Lang } from './settings.ts'

const FactSchema = z.strictObject({ text: z.string().min(1), q: z.array(z.number().int()).min(1) })
const LessonSchema = z.strictObject({
  topic: z.string(),
  common_sense: z.array(z.number().int()),
  hook: z.string().min(1),
  summary: z.array(z.string().min(1)).min(1),
  sections: z.array(z.strictObject({ title: z.string().min(1), facts: z.array(FactSchema).min(1) })).min(1),
  traps: z.array(FactSchema),
})
const LessonsFileSchema = z.strictObject({ description: z.string(), lessons: z.array(LessonSchema) })
export type Fact = z.infer<typeof FactSchema>
export type Lesson = z.infer<typeof LessonSchema>

export const LESSONS: Lesson[] = parse(LessonsFileSchema, lessonsJson as unknown, 'data/lessons.json').lessons
export const LESSON_BY_TOPIC = new Map(LESSONS.map((l) => [l.topic, l]))

/** Every text of a lesson in reading order (texts mark German terms as **bold**). */
function texts(l: Lesson): string[] {
  return [l.hook, ...l.summary, ...l.sections.flatMap((s) => [s.title, ...s.facts.map((f) => f.text)]), ...l.traps.map((t) => t.text)]
}

// Cross-file checks: one lesson per topic in topic order, each covering exactly its topic's questions.
if (LESSONS.map((l) => l.topic).join() !== TOPICS.map((t) => t.key).join()) {
  throw new Error('data/lessons.json must have one lesson per topic, in the order of data/topics.json')
}
for (const [i, l] of LESSONS.entries()) {
  const want = new Set(TOPICS[i].questions)
  const covered = new Set([...l.sections.flatMap((s) => s.facts), ...l.traps].flatMap((f) => f.q))
  const missing = [...want].filter((id) => !covered.has(id))
  const foreign = [...covered].filter((id) => !want.has(id))
  if (missing.length > 0 || foreign.length > 0) {
    throw new Error(`data/lessons.json: lesson ${l.topic} misses questions [${missing}] and lists other topics' [${foreign}]`)
  }
  const sense = new Set(l.common_sense)
  if (sense.size !== l.common_sense.length || l.common_sense.some((id) => !want.has(id))) {
    throw new Error(`data/lessons.json: common_sense of lesson ${l.topic} has duplicates or other topics' questions`)
  }
  const inFacts = new Set(l.sections.flatMap((s) => s.facts).flatMap((f) => f.q))
  for (const id of want) {
    if (QUESTION_BY_ID.get(id)?.image && !inFacts.has(id)) {
      throw new Error(`data/lessons.json: picture question ${id} of lesson ${l.topic} must be in a fact, not only in a trap (traps show no pictures)`)
    }
  }
  for (const t of texts(l)) {
    if (t.split('**').length % 2 === 0) throw new Error(`data/lessons.json: unbalanced ** in lesson ${l.topic}: "${t}"`)
  }
}

// ---------------------------------------------------------------- Russian
const LessonRuSchema = z.strictObject({
  topic: z.string(),
  hook: z.string().min(1),
  summary: z.array(z.string().min(1)),
  sections: z.array(z.strictObject({ title: z.string().min(1), facts: z.array(z.string().min(1)) })),
  traps: z.array(z.string().min(1)),
})
const LessonsRuFileSchema = z.strictObject({ description: z.string(), lessons: z.array(LessonRuSchema) })
type LessonRu = z.infer<typeof LessonRuSchema>
const LESSONS_RU_RAW = parse(LessonsRuFileSchema, lessonsRuJson as unknown, 'data/lessons_ru.json').lessons

/** The English lesson with the Russian texts. The translation must keep the structure, every number and every
 * **bold** term count, so a Russian fact can never drift from the questions it is attached to. */
function russian(l: Lesson, r: LessonRu): Lesson {
  const fail = (what: string): never => {
    throw new Error(`data/lessons_ru.json: lesson ${l.topic}: ${what}`)
  }
  if (r.topic !== l.topic) fail(`expected topic ${l.topic}, found ${r.topic} (same order as data/lessons.json)`)
  if (r.summary.length !== l.summary.length || r.traps.length !== l.traps.length || r.sections.length !== l.sections.length) {
    fail('summary, sections or traps differ in number from data/lessons.json')
  }
  r.sections.forEach((s, i) => s.facts.length !== l.sections[i].facts.length && fail(`section ${i + 1} has a different number of facts`))
  const out: Lesson = {
    ...l,
    hook: r.hook,
    summary: r.summary,
    sections: l.sections.map((s, i) => ({ title: r.sections[i].title, facts: s.facts.map((f, j) => ({ ...f, text: r.sections[i].facts[j] })) })),
    traps: l.traps.map((t, i) => ({ ...t, text: r.traps[i] })),
  }
  const nums = (t: string) => (t.match(/\d+/g) ?? []).sort().join()
  const en = texts(l)
  texts(out).forEach((t, i) => {
    if (nums(t) !== nums(en[i])) fail(`numbers differ from the English in "${t}"`)
    if (t.split('**').length !== en[i].split('**').length) fail(`**bold** terms differ from the English in "${t}"`)
  })
  return out
}

if (LESSONS_RU_RAW.length !== LESSONS.length) throw new Error('data/lessons_ru.json must have one lesson per lesson in data/lessons.json')
const LESSON_BY_LANG: Record<Lang, Map<string, Lesson>> = {
  en: LESSON_BY_TOPIC,
  ru: new Map(LESSONS.map((l, i) => [l.topic, russian(l, LESSONS_RU_RAW[i])])),
}

/** A topic's lesson in the explanation language. */
export function lessonIn(topicKey: string, lang: Lang): Lesson {
  const l = LESSON_BY_LANG[lang].get(topicKey)
  if (!l) throw new Error(`no lesson for topic ${topicKey}`)
  return l
}

// ---------------------------------------------------------------- the "why" after an answer
export type QuestionFact = { text: string; trap: boolean; topic: string }
const FACTS_BY_QUESTION: Record<Lang, Map<number, QuestionFact[]>> = { en: new Map(), ru: new Map() }
for (const lang of ['en', 'ru'] as const) {
  for (const l of LESSON_BY_LANG[lang].values()) {
    const facts = [...l.sections.flatMap((s) => s.facts.map((f) => ({ f, trap: false }))), ...l.traps.map((f) => ({ f, trap: true }))]
    for (const { f, trap } of facts) {
      for (const id of f.q) FACTS_BY_QUESTION[lang].set(id, [...(FACTS_BY_QUESTION[lang].get(id) ?? []), { text: f.text, trap, topic: l.topic }])
    }
  }
}

/** The lesson facts (and traps) that answer a question, in lesson order: the "why" shown after answering. */
export function factsFor(id: number, lang: Lang = 'en'): QuestionFact[] {
  const facts = FACTS_BY_QUESTION[lang].get(id)
  if (!facts) throw new Error(`no lesson fact covers question ${id}`)
  return facts
}

/** Whole minutes at 180 words per minute (an unhurried pace), at least 1. */
export function readingMinutes(l: Lesson): number {
  const words = texts(l).join(' ').replaceAll('**', '').split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 180))
}

/** Chance that a question is on the exam sheet: 30 of 300 general, 3 of 10 Bayern. */
export function drawChance(id: number): number {
  const q = QUESTION_BY_ID.get(id)
  if (!q) throw new Error(`question ${id} does not exist`)
  return q.section === 'Bayern' ? EXAM.bayern.draw / EXAM.bayern.pool : EXAM.general.draw / EXAM.general.pool
}

export type LessonStats = {
  questions: number
  /** Expected number of exam questions from this topic (all 24 lessons add up to 33). */
  points: number
  memorize: number
  memorizePoints: number
  /** Facts the memorize questions boil down to within this lesson (one "4 years" fact answers three questions). */
  facts: number
  commonSense: number
}

export function lessonStats(l: Lesson): LessonStats {
  const topic = TOPIC_BY_KEY.get(l.topic)
  if (!topic) throw new Error(`lesson ${l.topic} has no topic`)
  const sense = new Set(l.common_sense)
  const memo = topic.questions.filter((id) => !sense.has(id))
  // A fact counts if it brings a memorize question that no earlier fact or trap of the lesson covered.
  const seen = new Set<number>()
  let facts = 0
  for (const f of [...l.sections.flatMap((s) => s.facts), ...l.traps]) {
    const fresh = f.q.filter((id) => !sense.has(id) && !seen.has(id))
    if (fresh.length > 0) facts++
    for (const id of fresh) seen.add(id)
  }
  const sum = (ids: number[]) => ids.reduce((acc, id) => acc + drawChance(id), 0)
  return {
    questions: topic.questions.length,
    points: sum(topic.questions),
    memorize: memo.length,
    memorizePoints: sum(memo),
    facts,
    commonSense: sense.size,
  }
}

/** A fact whose questions are all common sense: fine to skim. */
export function isCommonSense(l: Lesson, f: Fact): boolean {
  return f.q.every((id) => l.common_sense.includes(id))
}
