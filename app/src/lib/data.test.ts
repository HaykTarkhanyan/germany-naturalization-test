import { describe, expect, it } from 'vitest'
import { BAYERN_IDS, english, GENERAL_IDS, imageUrl, QUESTIONS, TOPIC_OF_QUESTION, TOPICS } from './data.ts'

describe('data', () => {
  it('loads 300 general + 10 Bayern questions and 24 topics covering all of them', () => {
    expect(GENERAL_IDS).toHaveLength(300)
    expect(BAYERN_IDS).toHaveLength(10)
    expect(TOPICS).toHaveLength(24)
    expect(TOPIC_OF_QUESTION.size).toBe(310)
  })

  it('has an English question and four English options for every question', () => {
    for (const q of QUESTIONS) {
      const en = english(q)
      expect(en.question.length).toBeGreaterThan(0)
      expect(en.options).toHaveLength(4)
    }
    // spot checks that the option order follows the catalog, not the source dataset (DECISIONS.md #11)
    expect(english(QUESTIONS[70]).options[3]).toMatch(/^in Berlin/) // Q71: Berlin is option D
    expect(english(QUESTIONS[97]).options[1]).toMatch(/majority/) // Q98: "kann die Regierung ihre Mehrheit verlieren" is B
  })

  it('bundles an image for every picture question', () => {
    const withImages = QUESTIONS.filter((q) => q.image !== null)
    expect(withImages).toHaveLength(13)
    for (const q of withImages) expect(imageUrl(q)).toBeTruthy()
  })
})
