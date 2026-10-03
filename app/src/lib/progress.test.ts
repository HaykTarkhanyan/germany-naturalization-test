import { describe, expect, it } from 'vitest'
import { emptyProgress, parseProgress, ProgressError } from './progress.ts'

describe('parseProgress', () => {
  it('round-trips a valid document', () => {
    const p = emptyProgress()
    p.answers.push({ qid: 12, chosen: 2, correct: true, at: '2026-10-03T10:00:00.000Z', mode: 'practice' })
    expect(parseProgress(JSON.stringify(p), 'test')).toEqual(p)
  })

  it('rejects broken JSON and wrong shapes loudly', () => {
    expect(() => parseProgress('{oops', 'file')).toThrow(ProgressError)
    expect(() => parseProgress(JSON.stringify({ version: 2, answers: [] }), 'file')).toThrow(/does not look like study progress/)
    const bad = { ...emptyProgress(), answers: [{ qid: 999, chosen: 0, correct: true, at: 'x', mode: 'practice' }] }
    expect(() => parseProgress(JSON.stringify(bad), 'file')).toThrow(ProgressError)
  })
})
