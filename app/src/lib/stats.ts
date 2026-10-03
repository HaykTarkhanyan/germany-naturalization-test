// What the answers say about each question. A question is "known" when the last two answers to it were
// right: one right answer can be a lucky guess or a just-seen answer. The pass chance counts only known
// questions as sure and guesses everything else (DECISIONS.md #10).
import { BAYERN_IDS, GENERAL_IDS } from './data.ts'
import { expectedScore, passProbability } from './exam.ts'
import type { Answer } from './progress.ts'

export type Status = 'new' | 'learning' | 'known'

export function statusOf(history: readonly Answer[]): Status {
  if (history.length === 0) return 'new'
  const lastTwo = history.slice(-2)
  return lastTwo.length === 2 && lastTwo.every((a) => a.correct) ? 'known' : 'learning'
}

/** Status of every question id 1-310, from the answer log (kept in the order the answers were given). */
export function statusById(answers: readonly Answer[]): Map<number, Status> {
  const byQuestion = new Map<number, Answer[]>()
  for (const a of answers) {
    const list = byQuestion.get(a.qid)
    if (list) list.push(a)
    else byQuestion.set(a.qid, [a])
  }
  const result = new Map<number, Status>()
  for (let id = 1; id <= 310; id++) result.set(id, statusOf(byQuestion.get(id) ?? []))
  return result
}

export type Counts = Record<Status, number>

export function countStatuses(ids: readonly number[], statuses: ReadonlyMap<number, Status>): Counts {
  const counts: Counts = { new: 0, learning: 0, known: 0 }
  for (const id of ids) {
    const s = statuses.get(id)
    if (s === undefined) throw new Error(`no status for question ${id}`)
    counts[s] += 1
  }
  return counts
}

export function readiness(statuses: ReadonlyMap<number, Status>): { pass: number; expected: number; knownGeneral: number; knownBayern: number } {
  const knownGeneral = countStatuses(GENERAL_IDS, statuses).known
  const knownBayern = countStatuses(BAYERN_IDS, statuses).known
  return {
    pass: passProbability(knownGeneral, knownBayern),
    expected: expectedScore(knownGeneral, knownBayern),
    knownGeneral,
    knownBayern,
  }
}
