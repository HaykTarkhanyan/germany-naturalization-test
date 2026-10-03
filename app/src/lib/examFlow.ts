// Starting and finishing a mock exam. finishExam is pure (tested); the page applies its result.
import { BAYERN_IDS, GENERAL_IDS, QUESTION_BY_ID } from './data.ts'
import { drawExam, EXAM, scoreExam } from './exam.ts'
import type { ActiveExam, Answer, ExamResult } from './progress.ts'

export function newExam(now: number = Date.now()): ActiveExam {
  return {
    id: crypto.randomUUID(),
    startedAt: now,
    questionIds: drawExam(GENERAL_IDS, BAYERN_IDS),
    answers: Array.from({ length: EXAM.questions }, () => null),
  }
}

export function correctIndices(questionIds: readonly number[]): number[] {
  return questionIds.map((id) => {
    const q = QUESTION_BY_ID.get(id)
    if (!q) throw new Error(`exam contains unknown question ${id}`)
    return q.answer_index
  })
}

/** The finished exam, plus one answer-log entry per answered question (unanswered ones are not logged). */
export function finishExam(exam: ActiveExam, now: number, timedOut: boolean): { result: ExamResult; logged: Answer[] } {
  const correct = correctIndices(exam.questionIds)
  const score = scoreExam(exam.answers, correct)
  const at = new Date(now).toISOString()
  const logged: Answer[] = []
  exam.questionIds.forEach((qid, i) => {
    const chosen = exam.answers[i]
    if (chosen !== null) logged.push({ qid, chosen, correct: chosen === correct[i], at, mode: 'exam' })
  })
  return { result: { ...exam, finishedAt: now, score, passed: score >= EXAM.passMark, timedOut }, logged }
}

export function remainingMs(exam: ActiveExam, now: number): number {
  return exam.startedAt + EXAM.minutes * 60_000 - now
}

export function formatClock(ms: number): string {
  const s = Math.max(0, Math.ceil(ms / 1000))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}
