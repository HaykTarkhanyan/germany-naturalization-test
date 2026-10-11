import { describe, expect, it } from 'vitest'
import { QUESTION_BY_ID } from './data.ts'
import { KIND_LABELS, WORDS, wordsForShare } from './vocabulary.ts'

describe('vocabulary', () => {
  it('has a dictionary form and English meaning for every word, and only real question ids', () => {
    expect(WORDS.length).toBeGreaterThan(1000)
    for (const w of WORDS) {
      expect(w.de.length).toBeGreaterThan(0)
      expect(w.en.length).toBeGreaterThan(0)
      for (const id of w.questions) expect(QUESTION_BY_ID.has(id)).toBe(true)
    }
  })

  it('gives nouns their article', () => {
    const nouns = WORDS.filter((w) => w.kind === 'noun')
    const withArticle = nouns.filter((w) => /^(der|die|das) /.test(w.de))
    expect(withArticle.length / nouns.length).toBeGreaterThan(0.95)
    expect(WORDS.find((w) => w.lemma === 'Wahl')?.de).toBe('die Wahl')
  })

  it('computes how many frequent words cover a share of the text', () => {
    expect(wordsForShare(0.5)).toBeLessThan(wordsForShare(0.8))
    expect(wordsForShare(0.8)).toBeLessThan(wordsForShare(1))
  })

  it('lists every dictionary form once and files words under the right type', () => {
    const seen = new Map<string, string>()
    for (const w of WORDS) {
      expect(seen.get(w.de), `${w.de} is listed twice (${seen.get(w.de)}, ${w.key})`).toBeUndefined()
      seen.set(w.de, w.key)
    }
    expect(WORDS.find((w) => w.lemma === 'der')?.kind).toBe('function')
    expect(WORDS.find((w) => w.lemma === 'müssen')?.kind).toBe('verb')
    for (const w of WORDS) expect(KIND_LABELS[w.kind]).toBeTruthy()
  })
})
