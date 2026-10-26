import { describe, expect, it } from 'vitest'
import { TOPICS } from './data.ts'
import { factsFor, LESSON_BY_TOPIC, lessonIn, LESSONS, lessonStats, readingMinutes } from './lessons.ts'

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

describe('factsFor', () => {
  it('gives every exam question at least one lesson fact, traps marked', () => {
    for (let id = 1; id <= 310; id++) expect(factsFor(id).length, `question ${id}`).toBeGreaterThan(0)
    const all = Array.from({ length: 310 }, (_, i) => factsFor(i + 1)).flat()
    expect(all.some((f) => f.trap)).toBe(true)
    expect(() => factsFor(311)).toThrow()
  })
})

describe('Russian lessons', () => {
  const cyrillic = /[а-яё]/i
  it('has every lesson in Russian with the same questions, in the same places', () => {
    for (const l of LESSONS) {
      const ru = lessonIn(l.topic, 'ru')
      expect(cyrillic.test(ru.hook), l.topic).toBe(true)
      expect(ru.sections.map((s) => s.facts.map((f) => f.q))).toEqual(l.sections.map((s) => s.facts.map((f) => f.q)))
      expect(ru.traps.map((t) => t.q)).toEqual(l.traps.map((t) => t.q))
      expect(ru.common_sense).toEqual(l.common_sense)
    }
    expect(lessonIn('bayern', 'en')).toBe(LESSON_BY_TOPIC.get('bayern'))
  })

  it('gives the why in Russian for every question', () => {
    for (let id = 1; id <= 310; id++) {
      const ru = factsFor(id, 'ru')
      expect(ru.length).toBe(factsFor(id, 'en').length)
      expect(ru.every((f) => cyrillic.test(f.text)), `question ${id}`).toBe(true)
    }
  })
})
