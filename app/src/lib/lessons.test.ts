import { describe, expect, it } from 'vitest'
import { TOPICS } from './data.ts'
import { LESSON_BY_TOPIC, LESSONS, lessonStats, readingMinutes } from './lessons.ts'

describe('lessons', () => {
  it('has one lesson per topic that covers exactly the questions of its topic', () => {
    expect(LESSONS.map((l) => l.topic)).toEqual(TOPICS.map((t) => t.key))
    for (const [i, l] of LESSONS.entries()) {
      const covered = new Set([...l.sections.flatMap((s) => s.facts), ...l.traps].flatMap((f) => f.q))
      expect([...covered].sort((a, b) => a - b)).toEqual([...TOPICS[i].questions].sort((a, b) => a - b))
    }
  })

  it('splits the 33 exam points across the lessons', () => {
    const total = LESSONS.reduce((sum, l) => sum + lessonStats(l).points, 0)
    expect(total).toBeCloseTo(33, 9)
    expect(lessonStats(LESSONS[LESSONS.length - 1]).points).toBeCloseTo(3, 9) // Bayern: 10 questions x 3/10
  })

  it('counts memorize questions, facts and common sense (checked by hand for the Grundgesetz lesson)', () => {
    const s = lessonStats(LESSON_BY_TOPIC.get('grundgesetz_grundrechte')!)
    // memorize: 6+11 (one fact), 18, 7, 19, 274, 12 -> 7 questions in 6 facts
    expect(s).toMatchObject({ questions: 16, memorize: 7, facts: 6, commonSense: 9 })
    expect(s.points).toBeCloseTo(1.6, 9)
    expect(s.memorizePoints).toBeCloseTo(0.7, 9)
  })

  it('keeps every lesson short', () => {
    for (const l of LESSONS) expect(readingMinutes(l)).toBeLessThanOrEqual(3)
  })
})
