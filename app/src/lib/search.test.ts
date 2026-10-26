import { describe, expect, it } from 'vitest'
import { fold, searchQuestions } from './search.ts'

const ids = (q: string) => searchQuestions(q).map((x) => x.id)

describe('searchQuestions', () => {
  it('finds a question by its number', () => {
    expect(ids('128')).toEqual([128])
    expect(ids('Frage 309')).toEqual([309])
    expect(ids('Q128')).toEqual([128]) // the tag the lessons show
    expect(ids('999')).toEqual([])
  })
  it('needs every word, in German or English, ignoring case', () => {
    expect(ids('Wappen Bayern')).toContain(301)
    expect(ids('coat of arms bavaria')).toContain(301)
    expect(ids('Wappen Bayern').every((id) => ids('Wappen').includes(id))).toBe(true)
  })
  it('ignores umlauts and ß, so a keyboard without them works', () => {
    expect(fold('Übersetzer Straße')).toBe('ubersetzer strasse')
    expect(ids('ministerprasident')).toEqual(ids('Ministerpräsident'))
    expect(ids('ministerprasident').length).toBeGreaterThan(0)
  })
  it('finds nothing for an empty query', () => expect(ids('   ')).toEqual([]))
})
