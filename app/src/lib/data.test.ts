import { describe, expect, it } from 'vitest'
import { BAYERN_IDS, GENERAL_IDS, imageUrl, QUESTIONS, TOPIC_OF_QUESTION, TOPICS } from './data.ts'

describe('data', () => {
  it('loads 300 general + 10 Bayern questions and 24 topics covering all of them', () => {
    expect(GENERAL_IDS).toHaveLength(300)
    expect(BAYERN_IDS).toHaveLength(10)
    expect(TOPICS).toHaveLength(24)
    expect(TOPIC_OF_QUESTION.size).toBe(310)
  })

  it('bundles an image for every picture question', () => {
    const withImages = QUESTIONS.filter((q) => q.image !== null)
    expect(withImages).toHaveLength(13)
    for (const q of withImages) expect(imageUrl(q)).toBeTruthy()
  })
})
