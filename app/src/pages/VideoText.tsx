import { Fragment, useEffect } from 'react'
import { english, imageUrl, QUESTION_BY_ID, TOPIC_BY_KEY } from '../lib/data.ts'
import { LESSON_BY_TOPIC } from '../lib/lessons.ts'
import { link } from '../lib/router.ts'
import { updateSettings, useSettings } from '../lib/settings.ts'
import { narrationParts, VIDEO_LANGS, VIDEO_TEXT_BY_SLUG, VIDEO_TEXTS, videoReadingMinutes, type VideoText } from '../lib/videoTexts.ts'

const LANG_LABELS = { ru: 'Русский', en: 'English' } as const

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

/** Common-sense questions of the video's lessons (grey, as on the lesson pages). */
function commonSense(v: VideoText): Set<number> {
  return new Set(
    v.lessons.flatMap((key) => {
      const l = LESSON_BY_TOPIC.get(key)
      if (!l) throw new Error(`video ${v.slug} names lesson ${key}, which does not exist`)
      return l.common_sense
    }),
  )
}

/** The list of video texts, for the Learn page. */
export function VideoTextList() {
  const { videoLang } = useSettings()
  return VIDEO_TEXTS.map((v) => (
    <a key={v.slug} className="lesson-link" href={link('read', v.slug)}>
      <span>
        <b>
          {v.number} {v.title}
        </b>
      </span>
      <span className="lesson-meta">
        {videoReadingMinutes(v, videoLang)} min · {v.scenes.flatMap((s) => s.questions).length} questions ·{' '}
        {v.lessons.map((k) => TOPIC_BY_KEY.get(k)?.title_en ?? k).join(', ')}
      </span>
    </a>
  ))
}

/** #/read/<slug>: the narration of one video, with the exam answers it reveals. */
export function VideoTextPage({ slug }: { slug: string }) {
  // Block body on purpose (see LessonPage): scrollTo may return a Promise.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])
  const { videoLang, showEnglish } = useSettings()
  const v = VIDEO_TEXT_BY_SLUG.get(slug)
  if (!v) {
    return (
      <div className="card error">
        <p>There is no video text "{slug}".</p>
        <a href={link('learn')}>Learn</a>
      </div>
    )
  }
  const sense = commonSense(v)
  const ids = v.scenes.flatMap((s) => s.questions)
  const next = VIDEO_TEXTS[VIDEO_TEXTS.indexOf(v) + 1] ?? null
  return (
    <>
      <div className="practice-head">
        <a href={link('learn')}>← Learn</a>
        <span className="muted small">
          video {v.number} of {VIDEO_TEXTS.length}
        </span>
      </div>
      <div className="card">
        <h1>{v.title}</h1>
        <p className="muted small">
          Text of the video · {videoReadingMinutes(v, videoLang)} min read · answers {ids.length} exam questions · lessons:{' '}
          {v.lessons.map((k, i) => (
            <Fragment key={k}>
              {i > 0 && ', '}
              <a href={link('learn', k)}>{TOPIC_BY_KEY.get(k)?.title ?? k}</a>
            </Fragment>
          ))}
        </p>
        <div className="actions">
          {VIDEO_LANGS.map((lang) => (
            <button
              key={lang}
              type="button"
              className={`toggle ${videoLang === lang ? 'on' : ''}`}
              aria-pressed={videoLang === lang}
              onClick={() => updateSettings({ videoLang: lang })}
            >
              {LANG_LABELS[lang]}
            </button>
          ))}
        </div>
        <div className="toc">
          {v.scenes.map((s, i) => (
            <button key={i} type="button" className="linklike" onClick={() => scrollTo(`video-s${i}`)}>
              {s.title}
            </button>
          ))}
        </div>
      </div>
      {v.scenes.map((s, i) => {
        const parts = narrationParts(s.voice[videoLang])
        return (
          <details open key={i} id={`video-s${i}`} className="card lesson-section">
            <summary>
              <h2>{s.title}</h2>
            </summary>
            <p className="term-line">{s.screen}</p>
            <p className="narration">
              {parts.map((p, j) =>
                typeof p === 'number' ? (
                  <span key={j} className="qref" title="Exam question answered here, shown below">
                    <span className={sense.has(p) ? 'q-sense' : 'q-memo'}>Q{p}</span>
                  </span>
                ) : (
                  <Fragment key={j}>{p}</Fragment>
                ),
              )}
            </p>
            {s.questions.length > 0 && (
              <ul className="answers">
                {parts
                  .filter((p): p is number => typeof p === 'number')
                  .map((id) => (
                    <Answer key={id} id={id} grey={sense.has(id)} showEnglish={showEnglish} />
                  ))}
              </ul>
            )}
          </details>
        )
      })}
      <div className="card">
        <div className="actions">
          <a className="button primary" href={link('practice', 'list', ids.join(','))}>
            Practice these {ids.length} questions
          </a>
          {next && (
            <a className="button" href={link('read', next.slug)}>
              Next: {next.number} {next.title} →
            </a>
          )}
        </div>
      </div>
    </>
  )
}

/** One revealed exam question: German question, picture, correct answer (English under each when on). */
function Answer({ id, grey, showEnglish }: { id: number; grey: boolean; showEnglish: boolean }) {
  const q = QUESTION_BY_ID.get(id)
  if (!q) throw new Error(`video text refers to unknown question ${id}`)
  const en = english(q)
  const img = imageUrl(q)
  const answer = q.options[q.answer_index]
  const answerEn = en.options[q.answer_index]
  return (
    <li className={grey ? 'sense' : undefined}>
      <span className="muted small">
        Frage {id}
        {q.section === 'Bayern' ? ' (Bayern)' : ''}
        {grey ? ' · common sense' : ''}
      </span>
      <span className="answer-q">{q.question}</span>
      {showEnglish && <span className="en">{en.question}</span>}
      {img && <img className="fact-img" src={img} alt={`Bild zu Frage ${id}`} loading="lazy" />}
      <span className="answer-a">
        ✓ {answer}
        {/* Picture labels ("Bild 1") need no translation line, as in QuestionCard. */}
        {showEnglish && answerEn !== answer && !/^(Image )?\d$/.test(answerEn) && <span className="en">{answerEn}</span>}
      </span>
    </li>
  )
}
