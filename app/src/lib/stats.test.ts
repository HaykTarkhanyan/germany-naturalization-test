import { describe, expect, it } from 'vitest'
import type { Answer } from './progress.ts'
import { countStatuses, readiness, statusById, statusOf } from './stats.ts'

const answer = (qid: number, correct: boolean): Answer => ({ qid, chosen: 0, correct, at: '2026-10-03T00:00:00Z', mode: 'practice' })

describe('statusOf', () => {
  it('is new without answers', () => expect(statusOf([])).toBe('new'))
  it('is learning after one right answer', () => expect(statusOf([answer(1, true)])).toBe('learning'))
  it('is known after the last two answers were right', () => {
    expect(statusOf([answer(1, false), answer(1, true), answer(1, true)])).toBe('known')
  })
  it('falls back to learning after a wrong answer', () => {
    expect(statusOf([answer(1, true), answer(1, true), answer(1, false)])).toBe('learning')
  })
})

describe('statusById / readiness', () => {
  it('covers all 310 ids and feeds the exam model', () => {
    const answers = [answer(5, true), answer(5, true), answer(301, true), answer(301, true), answer(7, true)]
    const statuses = statusById(answers)
    expect(statuses.size).toBe(310)
    expect(countStatuses([5, 7, 9, 301], statuses)).toEqual({ known: 2, learning: 1, new: 1 })
    const r = readiness(statuses)
    expect(r.knownGeneral).toBe(1)
    expect(r.knownBayern).toBe(1)
    expect(r.pass).toBeGreaterThan(0)
  })
})
