import { describe, expect, it } from 'vitest'
import { drawExam, expectedScore, passProbability, scoreExam } from './exam.ts'

const general = Array.from({ length: 300 }, (_, i) => i + 1)
const bayern = Array.from({ length: 10 }, (_, i) => i + 301)

function seeded(seed: number): () => number {
  let s = seed
  return () => {
    s = (s * 1103515245 + 12345) % 2 ** 31
    return s / 2 ** 31
  }
}

describe('passProbability', () => {
  // Reference values from an independent Python implementation (math.comb, exact sums), and they match
  // scripts/mine_patterns.py: blind guessing 0.00095, "every second question memorized" 0.9361.
  it.each([
    [0, 0, 0.0009509599956171568],
    [150, 5, 0.9360898856228623],
    [100, 10, 0.712543548856813],
    [60, 0, 0.0865815150090801],
    [300, 10, 1],
  ])('known %i general + %i Bayern -> %f', (g, b, expected) => {
    expect(passProbability(g, b)).toBeCloseTo(expected, 10)
  })

  it('rejects impossible counts', () => {
    expect(() => passProbability(301, 0)).toThrow()
    expect(() => passProbability(0, 11)).toThrow()
  })
})

describe('expectedScore', () => {
  it('is 8.25 when guessing everything and 33 when knowing everything', () => {
    expect(expectedScore(0, 0)).toBeCloseTo(8.25, 10)
    expect(expectedScore(300, 10)).toBeCloseTo(33, 10)
  })
})

describe('drawExam', () => {
  it('draws 30 distinct general and 3 distinct Bayern questions', () => {
    for (let seed = 1; seed <= 20; seed++) {
      const ids = drawExam(general, bayern, seeded(seed))
      expect(ids).toHaveLength(33)
      expect(new Set(ids).size).toBe(33)
      expect(ids.filter((id) => id <= 300)).toHaveLength(30)
      expect(ids.filter((id) => id > 300)).toHaveLength(3)
    }
  })

  it('needs the full pools', () => {
    expect(() => drawExam(general.slice(1), bayern)).toThrow()
  })
})

describe('scoreExam', () => {
  it('counts matching answers; unanswered is wrong', () => {
    expect(scoreExam([0, 1, null, 3], [0, 2, 1, 3])).toBe(2)
  })
})
