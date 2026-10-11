// The German vocabulary of the catalog (data/vocabulary.json, scripts/build_vocabulary.py) with the dictionary form and
// English meaning of every word (data/vocabulary_en.json, scripts/translate_vocabulary.py), validated at startup.
import { z } from 'zod'
import vocabularyJson from '../../../data/vocabulary.json' with { type: 'json' }
import englishJson from '../../../data/vocabulary_en.json' with { type: 'json' }
import { parse, QUESTION_BY_ID } from './data.ts'

const KINDS = ['noun', 'verb', 'adjective', 'adverb', 'function', 'other'] as const
const WordSchema = z.strictObject({
  key: z.string().min(1),
  lemma: z.string().min(1),
  kind: z.enum(KINDS),
  count: z.number().int().min(1),
  forms: z.array(z.string().min(1)).min(1),
  questions: z.array(z.number().int()).min(1),
  core: z.boolean(),
})
const VocabularyFileSchema = z.strictObject({
  description: z.string(),
  names_and_places_excluded: z.number().int().min(0),
  abbreviations_excluded: z.array(z.string()),
  words: z.array(WordSchema).min(1),
})
const EnglishFileSchema = z.strictObject({
  description: z.string(),
  words: z.record(z.string(), z.strictObject({ de: z.string().min(1), en: z.string().min(1), type: z.enum(KINDS) })),
})
export type WordKind = (typeof KINDS)[number]
/** Filter labels for the Words page; a test checks every word type in the data has one. */
export const KIND_LABELS: Record<WordKind, string> = {
  noun: 'Nouns',
  verb: 'Verbs',
  adjective: 'Adjectives',
  adverb: 'Adverbs',
  function: 'Small words (der, und, mit ...)',
  other: 'Other',
}
export type Word = z.infer<typeof WordSchema> & { de: string; en: string }

const file = parse(VocabularyFileSchema, vocabularyJson as unknown, 'data/vocabulary.json')
const english = parse(EnglishFileSchema, englishJson as unknown, 'data/vocabulary_en.json').words

export const WORDS: Word[] = file.words.map((w) => {
  const t = english[w.key]
  if (!t) throw new Error(`data/vocabulary_en.json has no translation for ${w.key} (run scripts/translate_vocabulary.py)`)
  const missing = w.questions.filter((id) => !QUESTION_BY_ID.has(id))
  if (missing.length > 0) throw new Error(`data/vocabulary.json: ${w.key} refers to unknown questions ${missing}`)
  return { ...w, de: t.de, en: t.en }
})
// (vocabulary_en.json also holds rows that were merged into another word: data/vocabulary_raw.json)
if (new Set(WORDS.map((w) => w.key)).size !== WORDS.length) throw new Error('data/vocabulary.json has duplicate keys')

export const NAMES_EXCLUDED = file.names_and_places_excluded
export const ABBREVIATIONS_EXCLUDED = file.abbreviations_excluded

/** How many of the most frequent words make up the given share of all running text. */
export function wordsForShare(share: number): number {
  const counts = WORDS.map((w) => w.count).sort((a, b) => b - a)
  const total = counts.reduce((s, c) => s + c, 0)
  let sum = 0
  for (const [i, c] of counts.entries()) {
    sum += c
    if (sum / total >= share) return i + 1
  }
  return counts.length
}
