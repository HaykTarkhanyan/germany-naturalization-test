// The exam: 30 of the 300 general questions + 3 of the 10 Bayern questions, 60 minutes, 17 correct pass.
// passProbability is the exact model from scripts/mine_patterns.py (multivariate hypergeometric draw,
// binomial tail for guesses), reduced to two kinds of question: known (always right) and not known
// (a blind guess, right with p = 0.25).

export const EXAM = {
  general: { pool: 300, draw: 30 },
  bayern: { pool: 10, draw: 3 },
  questions: 33,
  passMark: 17,
  minutes: 60,
} as const

const GUESS = 0.25

export function shuffle<T>(items: readonly T[], rand: () => number = Math.random): T[] {
  const a = [...items]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

/** A random exam sheet: 30 general + 3 Bayern question ids, in random order. */
export function drawExam(generalIds: readonly number[], bayernIds: readonly number[], rand: () => number = Math.random): number[] {
  if (generalIds.length !== EXAM.general.pool || bayernIds.length !== EXAM.bayern.pool) {
    throw new Error(`drawExam needs ${EXAM.general.pool} general and ${EXAM.bayern.pool} Bayern ids`)
  }
  const general = shuffle(generalIds, rand).slice(0, EXAM.general.draw)
  const bayern = shuffle(bayernIds, rand).slice(0, EXAM.bayern.draw)
  return shuffle([...general, ...bayern], rand)
}

export function scoreExam(answers: readonly (number | null)[], correct: readonly number[]): number {
  if (answers.length !== correct.length) throw new Error('scoreExam: answers and correct indices differ in length')
  return answers.reduce<number>((n, a, i) => n + (a === correct[i] ? 1 : 0), 0)
}

function comb(n: number, k: number): number {
  if (k < 0 || k > n) return 0
  let r = 1
  for (let i = 1; i <= k; i++) r = (r * (n - k + i)) / i
  return r
}

/** P(at least k successes in n draws with p = 0.25). */
function guessTail(n: number, k: number): number {
  let p = 0
  for (let i = Math.max(k, 0); i <= n; i++) p += comb(n, i) * GUESS ** i * (1 - GUESS) ** (n - i)
  return p
}

/** Distribution of the number of known questions on the sheet, for one part of the pool. */
function knownDrawn(known: number, pool: number, draw: number): number[] {
  if (known < 0 || known > pool) throw new Error(`known=${known} is outside 0..${pool}`)
  const total = comb(pool, draw)
  return Array.from({ length: draw + 1 }, (_, i) => (comb(known, i) * comb(pool - known, draw - i)) / total)
}

/** Exact chance to pass when `knownGeneral` general and `knownBayern` Bayern questions are known and the rest is guessed. */
export function passProbability(knownGeneral: number, knownBayern: number): number {
  const g = knownDrawn(knownGeneral, EXAM.general.pool, EXAM.general.draw)
  const b = knownDrawn(knownBayern, EXAM.bayern.pool, EXAM.bayern.draw)
  let p = 0
  for (let i = 0; i < g.length; i++) {
    for (let j = 0; j < b.length; j++) {
      if (g[i] === 0 || b[j] === 0) continue
      p += g[i] * b[j] * guessTail(EXAM.questions - i - j, EXAM.passMark - i - j)
    }
  }
  return Math.min(p, 1)
}

export function expectedScore(knownGeneral: number, knownBayern: number): number {
  const part = (known: number, pool: number, draw: number) => (draw * (known + GUESS * (pool - known))) / pool
  return part(knownGeneral, EXAM.general.pool, EXAM.general.draw) + part(knownBayern, EXAM.bayern.pool, EXAM.bayern.draw)
}
