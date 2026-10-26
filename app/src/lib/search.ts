// Find exam questions by number ("128", "Frage 128", "Q128") or by words in the German or English question and options.
// Case, umlauts and ß are ignored ("ubersetzer" finds "Übersetzer"), so a phone keyboard without umlauts works.
import { english, QUESTIONS, type Question } from './data.ts'

/** Lower case, umlauts and accents dropped (ä -> a), ß -> ss. */
export function fold(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ß/g, 'ss')
}

const HAYSTACK = new Map(
  QUESTIONS.map((q) => {
    const en = english(q)
    return [q.id, fold([q.question, ...q.options, en.question, ...en.options].join(' \n '))]
  }),
)

/** Questions matching every word of the query, in catalog order; a bare number (or "Frage N", "QN") is that question. */
export function searchQuestions(query: string): Question[] {
  const q = fold(query.trim())
  const num = /^(?:frage\s*|q\s*)?(\d{1,3})$/.exec(q)   // "128", "Frage 128", "Q128" (the lessons' tags)
  if (num) return QUESTIONS.filter((x) => x.id === Number(num[1]))
  const words = q.split(/\s+/).filter(Boolean)
  if (words.length === 0) return []
  return QUESTIONS.filter((x) => {
    const hay = HAYSTACK.get(x.id)
    if (hay === undefined) throw new Error(`no search text for question ${x.id}`)
    return words.every((w) => hay.includes(w))
  })
}
