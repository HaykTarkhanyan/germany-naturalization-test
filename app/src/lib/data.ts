// The question pool and the study topics, read from ../data (built by scripts/build_dataset.py and
// hand-curated in data/topics.json) and validated at startup. Any inconsistency throws.
import { z } from 'zod'
import questionsJson from '../../../data/questions_bayern.json' with { type: 'json' }
import topicsJson from '../../../data/topics.json' with { type: 'json' }
import translationsJson from '../../../data/translations_en.json' with { type: 'json' }

const QuestionSchema = z.strictObject({
  id: z.number().int().min(1).max(310),
  section: z.enum(['general', 'Bayern']),
  catalog_number: z.number().int().min(1),
  question: z.string().min(1),
  options: z.array(z.string().min(1)).length(4),
  options_oet: z.array(z.string().min(1)).length(4),
  answer_index: z.number().int().min(0).max(3),
  answer: z.string().min(1),
  image: z.string().nullable(),
})
export type Question = z.infer<typeof QuestionSchema>

const ModuleSchema = z.strictObject({ key: z.string(), title: z.string(), title_en: z.string() })
const TopicSchema = z.strictObject({
  key: z.string(),
  module: z.string(),
  title: z.string(),
  title_en: z.string(),
  questions: z.array(z.number().int()).min(1),
})
const TopicsFileSchema = z.strictObject({
  description: z.string(),
  modules: z.array(ModuleSchema).min(1),
  topics: z.array(TopicSchema).min(1),
})
export type Module = z.infer<typeof ModuleSchema>
export type Topic = z.infer<typeof TopicSchema>

export function parse<T>(schema: z.ZodType<T>, data: unknown, file: string): T {
  const result = schema.safeParse(data)
  if (!result.success) {
    const issues = result.error.issues.map((i) => `${i.path.join('.') || '(root)'}: ${i.message}`)
    throw new Error(`${file} is invalid: ${issues.slice(0, 5).join('; ')}`)
  }
  return result.data
}

export const QUESTIONS: Question[] = parse(z.array(QuestionSchema).length(310), questionsJson as unknown, 'data/questions_bayern.json')
const topicsFile = parse(TopicsFileSchema, topicsJson as unknown, 'data/topics.json')
export const MODULES: Module[] = topicsFile.modules
export const TOPICS: Topic[] = topicsFile.topics

export const QUESTION_BY_ID = new Map(QUESTIONS.map((q) => [q.id, q]))
export const GENERAL_IDS = QUESTIONS.filter((q) => q.section === 'general').map((q) => q.id)
export const BAYERN_IDS = QUESTIONS.filter((q) => q.section === 'Bayern').map((q) => q.id)
export const TOPIC_BY_KEY = new Map(TOPICS.map((t) => [t.key, t]))
export const TOPIC_OF_QUESTION = new Map(TOPICS.flatMap((t) => t.questions.map((id) => [id, t] as const)))

// Cross-file checks the schemas cannot express.
for (const [i, q] of QUESTIONS.entries()) {
  if (q.id !== i + 1) throw new Error(`data/questions_bayern.json: entry ${i} has id ${q.id}, expected ${i + 1}`)
  if (q.options[q.answer_index] !== q.answer) throw new Error(`question ${q.id}: answer does not match options[answer_index]`)
}
if (GENERAL_IDS.length !== 300 || BAYERN_IDS.length !== 10) {
  throw new Error(`expected 300 general + 10 Bayern questions, got ${GENERAL_IDS.length} + ${BAYERN_IDS.length}`)
}
const moduleKeys = new Set(MODULES.map((m) => m.key))
for (const t of TOPICS) {
  if (!moduleKeys.has(t.module)) throw new Error(`data/topics.json: topic ${t.key} has unknown module ${t.module}`)
}
const listed = TOPICS.flatMap((t) => t.questions)
if (listed.length !== 310 || new Set(listed).size !== 310 || listed.some((id) => !QUESTION_BY_ID.has(id))) {
  throw new Error('data/topics.json must list every question id 1-310 exactly once')
}

// English translations (scripts/build_translations.py), options in catalog order like the German ones.
const EnglishSchema = z.strictObject({ question: z.string().min(1), options: z.array(z.string().min(1)).length(4) })
const TranslationsFileSchema = z.strictObject({ source: z.string(), translations: z.record(z.string(), EnglishSchema) })
export type English = z.infer<typeof EnglishSchema>
const translations = parse(TranslationsFileSchema, translationsJson as unknown, 'data/translations_en.json').translations
export const ENGLISH = new Map<number, English>()
for (const q of QUESTIONS) {
  const en = translations[String(q.id)]
  if (en === undefined) throw new Error(`data/translations_en.json has no translation for question ${q.id}`)
  ENGLISH.set(q.id, en)
}

export function english(q: Question): English {
  const en = ENGLISH.get(q.id)
  if (en === undefined) throw new Error(`no English translation for question ${q.id}`)
  return en
}

// Picture questions: the images are bundled by Vite (hashed URLs in the build).
const IMAGE_URLS = import.meta.glob('../../../data/images/*.png', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>

export function imageUrl(q: Question): string | null {
  if (q.image === null) return null
  const url = IMAGE_URLS[`../../../${q.image}`]
  if (url === undefined) throw new Error(`question ${q.id}: image ${q.image} is not bundled`)
  return url
}
