import { describe, expect, it } from 'vitest'
import { QUESTIONS, TOPICS } from './data.ts'
import { narrationParts, VIDEO_TEXTS, videoForLesson, videoReadingMinutes } from './videoTexts.ts'

describe('video texts', () => {
  it('reads all 14 video scripts in order', () => {
    expect(VIDEO_TEXTS.map((v) => v.number)).toEqual(Array.from({ length: 14 }, (_, i) => String(i + 1).padStart(2, '0')))
    expect(VIDEO_TEXTS[11]).toMatchObject({ slug: '12_ddr', title: 'Die DDR', lessons: ['ddr'] })
    expect(VIDEO_TEXTS[11].scenes[1].title).toBe('2. The state') // the "(~29 s)" timing is dropped
  })

  it('answers every exam question exactly once across the series', () => {
    const answered = VIDEO_TEXTS.flatMap((v) => v.scenes.flatMap((s) => s.questions)).sort((a, b) => a - b)
    expect(answered).toEqual(QUESTIONS.map((q) => q.id).sort((a, b) => a - b))
  })

  it('gives every lesson exactly one video', () => {
    for (const t of TOPICS) expect(VIDEO_TEXTS.filter((v) => v.lessons.includes(t.key)), t.key).toHaveLength(1)
    expect(videoForLesson('bayern')?.slug).toBe('01_bayern')
  })

  it('splits narration at the {Q} markers', () => {
    expect(narrationParts('DDR. {Q190} Founded {Q172} in 1949.')).toEqual(['DDR. ', 190, ' Founded ', 172, ' in 1949.'])
    expect(narrationParts('No answers here.')).toEqual(['No answers here.'])
  })

  it('has both languages for every scene and a short read per video', () => {
    for (const v of VIDEO_TEXTS) {
      for (const s of v.scenes) expect(s.voice.ru.length > 0 && s.voice.en.length > 0, `${v.slug} ${s.title}`).toBe(true)
      expect(videoReadingMinutes(v, 'en')).toBeLessThanOrEqual(6)
    }
  })
})
