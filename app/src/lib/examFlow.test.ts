import { describe, expect, it } from 'vitest'
import { correctIndices, finishExam, formatClock, newExam, remainingMs } from './examFlow.ts'

describe('finishExam', () => {
  it('scores, passes at 17 and logs only answered questions', () => {
    const exam = newExam(1_000)
    const correct = correctIndices(exam.questionIds)
    // 17 right, 5 wrong, 11 unanswered
    exam.answers = correct.map((c, i) => (i < 17 ? c : i < 22 ? (c + 1) % 4 : null))
    const { result, logged } = finishExam(exam, 61_000, false)
    expect(result.score).toBe(17)
    expect(result.passed).toBe(true)
    expect(logged).toHaveLength(22)
    expect(logged.filter((a) => a.correct)).toHaveLength(17)
    expect(logged.every((a) => a.mode === 'exam')).toBe(true)
  })

  it('fails at 16', () => {
    const exam = newExam(0)
    const correct = correctIndices(exam.questionIds)
    exam.answers = correct.map((c, i) => (i < 16 ? c : null))
    expect(finishExam(exam, 1, true).result).toMatchObject({ score: 16, passed: false, timedOut: true })
  })

  it('ends a timed-out exam at its deadline, not when the app is opened again', () => {
    const exam = newExam(0)
    exam.answers[0] = 1
    const threeHoursLater = 3 * 3_600_000
    const { result, logged } = finishExam(exam, threeHoursLater, true)
    expect(result.finishedAt).toBe(3_600_000)
    expect(formatClock(result.finishedAt - result.startedAt)).toBe('60:00')
    expect(logged[0].at).toBe(new Date(3_600_000).toISOString())
  })
})

describe('timer', () => {
  it('counts down 60 minutes and formats m:ss', () => {
    const exam = newExam(0)
    expect(remainingMs(exam, 0)).toBe(3_600_000)
    expect(formatClock(remainingMs(exam, 3_600_000 - 61_000))).toBe('1:01')
    expect(formatClock(-5)).toBe('0:00')
  })
})
