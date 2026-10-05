import { Fragment, useEffect } from 'react'
import { BAYERN_IDS, imageUrl, MODULES, QUESTION_BY_ID, TOPIC_BY_KEY, TOPICS } from '../lib/data.ts'
import { EXAM, GUESS, passProbability } from '../lib/exam.ts'
import {
  drawChance,
  isCommonSense,
  LESSON_BY_TOPIC,
  LESSONS,
  lessonStats,
  readingMinutes,
  type Fact,
  type Lesson,
  type LessonStats,
} from '../lib/lessons.ts'
import { link } from '../lib/router.ts'

const STATS = new Map(LESSONS.map((l) => [l.topic, lessonStats(l)]))
const TOTAL_MINUTES = LESSONS.reduce((sum, l) => sum + readingMinutes(l), 0)
const TOTAL = [...STATS.values()].reduce(
  (t, s) => ({
    questions: t.questions + s.questions,
    points: t.points + s.points,
    memorize: t.memorize + s.memorize,
    memorizePoints: t.memorizePoints + s.memorizePoints,
    facts: t.facts + s.facts,
    commonSense: t.commonSense + s.commonSense,
  }),
  { questions: 0, points: 0, memorize: 0, memorizePoints: 0, facts: 0, commonSense: 0 },
)

// "Common sense only": every common-sense question right, every other one a blind guess.
const SENSE = new Set(LESSONS.flatMap((l) => l.common_sense))
const SENSE_BAYERN = BAYERN_IDS.filter((id) => SENSE.has(id)).length
const SENSE_PASS = passProbability(SENSE.size - SENSE_BAYERN, SENSE_BAYERN)
const SENSE_EXPECTED = [...QUESTION_BY_ID.keys()].reduce((sum, id) => sum + drawChance(id) * (SENSE.has(id) ? 1 : GUESS), 0)

const fmt = (x: number) => x.toFixed(1)

function lessonOf(topicKey: string): Lesson {
  const l = LESSON_BY_TOPIC.get(topicKey)
  if (!l) throw new Error(`no lesson for topic ${topicKey}`)
  return l
}

function statsOf(topicKey: string): LessonStats {
  const s = STATS.get(topicKey)
  if (!s) throw new Error(`no lesson for topic ${topicKey}`)
  return s
}

/** Renders "a **b** c" with b in bold. */
function Rich({ text }: { text: string }) {
  return <>{text.split('**').map((part, i) => (i % 2 === 1 ? <b key={i}>{part}</b> : part))}</>
}

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

/** #/learn: where the points are, then all lessons by module. */
export function Learn() {
  return (
    <>
      <div className="card">
        <h1>Learn</h1>
        <p className="muted">
          One short read per topic, about {TOTAL_MINUTES} minutes for all 24. Each lesson covers every exam question of its topic, so
          the practice round afterwards is mostly recognition.
        </p>
        <p>
          <b>{TOTAL.commonSense} of 310</b> questions are common sense: the wrong options are absurd. The other <b>{TOTAL.memorize}</b>{' '}
          boil down to <b>{TOTAL.facts} facts</b> worth memorizing (counted per lesson, so a few like "18" repeat across lessons). Common sense alone, with blind guesses on the rest, averages about{' '}
          {fmt(SENSE_EXPECTED)} of {EXAM.questions} ({EXAM.passMark} pass), a {Math.round(100 * SENSE_PASS)}% pass chance. That holds
          only if my common-sense calls are right and you read the German correctly. The facts are what make the pass safe.
        </p>
        <div className="toc">
          <button type="button" className="linklike" onClick={() => scrollTo('learn-points')}>
            Where the points are
          </button>
          {MODULES.map((m) => (
            <button key={m.key} type="button" className="linklike" onClick={() => scrollTo(`learn-${m.key}`)}>
              {m.title}
            </button>
          ))}
        </div>
      </div>
      <details open id="learn-points" className="card module learn-module">
        <summary>
          <span className="module-title">Where the points are</span>
        </summary>
        <p className="muted small">
          <b>Points</b>: how many of your {EXAM.questions} exam questions come from the topic on average (each general question has a{' '}
          {EXAM.general.draw} in {EXAM.general.pool} chance to be on your sheet, each Bayern question {EXAM.bayern.draw} in{' '}
          {EXAM.bayern.pool}). <b>Memorize</b>: questions with a believable wrong option. <b>Facts</b>: what those boil down to within the
          lesson (one "4 years" fact answers three questions). <b>Sense</b>: common sense. The split is my judgment, not official.
        </p>
        <table className="points-table">
          <colgroup>
            <col style={{ width: '35%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '13%' }} />
            <col style={{ width: '13%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>Lesson</th>
              <th className="num">Questions</th>
              <th className="num">Points</th>
              <th className="num">Memorize</th>
              <th className="num">Facts</th>
              <th className="num">Sense</th>
            </tr>
          </thead>
          <tbody>
            {MODULES.map((m) => (
              <Fragment key={m.key}>
                <tr className="group">
                  <td colSpan={6}>{m.title}</td>
                </tr>
                {TOPICS.filter((t) => t.module === m.key).map((t) => {
                  const s = statsOf(t.key)
                  return (
                    <tr key={t.key}>
                      <td>
                        <a href={link('learn', t.key)}>{t.title}</a>
                      </td>
                      <td className="num">{s.questions}</td>
                      <td className="num">{fmt(s.points)}</td>
                      <td className="num">{s.memorize}</td>
                      <td className="num">{s.facts}</td>
                      <td className="num">{s.commonSense}</td>
                    </tr>
                  )
                })}
              </Fragment>
            ))}
            <tr className="total">
              <td>All 24</td>
              <td className="num">{TOTAL.questions}</td>
              <td className="num">{fmt(TOTAL.points)}</td>
              <td className="num">{TOTAL.memorize}</td>
              <td className="num">{TOTAL.facts}</td>
              <td className="num">{TOTAL.commonSense}</td>
            </tr>
          </tbody>
        </table>
      </details>
      {MODULES.map((m) => {
        const topics = TOPICS.filter((t) => t.module === m.key)
        const minutes = topics.reduce((sum, t) => sum + readingMinutes(lessonOf(t.key)), 0)
        return (
          <details open key={m.key} id={`learn-${m.key}`} className="card module learn-module">
            <summary>
              <span className="module-title">{m.title}</span>{' '}
              <span className="muted small">
                {m.title_en} · {minutes} min
              </span>
            </summary>
            {topics.map((t) => {
              const l = lessonOf(t.key)
              const s = statsOf(t.key)
              return (
                <a key={t.key} className="lesson-link" href={link('learn', t.key)}>
                  <span>
                    <b>{t.title}</b> <span className="muted small">{t.title_en}</span>
                  </span>
                  <span className="lesson-meta">
                    {readingMinutes(l)} min · {s.questions} questions · ≈{fmt(s.points)} points · {s.memorize} to memorize ({s.facts}{' '}
                    facts)
                  </span>
                  <span className="lesson-teaser">{l.hook}</span>
                </a>
              )
            })}
          </details>
        )
      })}
    </>
  )
}

/** #/learn/<topic>: the lesson for one topic. */
export function LessonPage({ topicKey }: { topicKey: string }) {
  // Hash navigation keeps the scroll position, so "Next lesson" at the bottom would open mid-page.
  // Block body on purpose: newer Chromium returns a Promise from scrollTo, which React would take as a cleanup.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  const topic = TOPIC_BY_KEY.get(topicKey)
  if (!topic) {
    return (
      <div className="card error">
        <p>There is no lesson "{topicKey}".</p>
        <a href={link('learn')}>All lessons</a>
      </div>
    )
  }
  const lesson = lessonOf(topic.key)
  const s = statsOf(topic.key)
  const idx = TOPICS.indexOf(topic)
  const next = TOPICS[idx + 1] ?? null
  const module = MODULES.find((m) => m.key === topic.module)
  return (
    <>
      <div className="practice-head">
        <a href={link('learn')}>← All lessons</a>
        <span className="muted small">
          {module?.title} · lesson {idx + 1} of {TOPICS.length}
        </span>
      </div>
      <div className="card">
        <h1>{topic.title}</h1>
        <p className="muted small">
          {topic.title_en} · {readingMinutes(lesson)} min read · covers all {s.questions} exam questions of this topic
        </p>
        <div className="stats">
          <div>
            <b>{s.questions}</b> questions
          </div>
          <div title={`Of your ${EXAM.questions} exam questions, this many come from this topic on average`}>
            <b>≈{fmt(s.points)}</b> exam points
          </div>
          <div>
            <b>{s.memorize}</b> to memorize: {s.facts} facts, ≈{fmt(s.memorizePoints)} points
          </div>
          <div>
            <b>{s.commonSense}</b> common sense (grey below)
          </div>
        </div>
        <p className="lesson-hook">{lesson.hook}</p>
        <div className="sixty">
          <h2>In 60 seconds</h2>
          <ul>
            {lesson.summary.map((line, i) => (
              <li key={i}>
                <Rich text={line} />
              </li>
            ))}
          </ul>
        </div>
        <div className="toc">
          {lesson.sections.map((sec, i) => (
            <button key={i} type="button" className="linklike" onClick={() => scrollTo(`lesson-s${i}`)}>
              {sec.title}
            </button>
          ))}
          {lesson.traps.length > 0 && (
            <button type="button" className="linklike" onClick={() => scrollTo('lesson-traps')}>
              Watch out
            </button>
          )}
        </div>
      </div>
      {lesson.sections.map((sec, i) => (
        <details open key={i} id={`lesson-s${i}`} className="card lesson-section">
          <summary>
            <h2>{sec.title}</h2>
          </summary>
          <Facts lesson={lesson} facts={sec.facts} images />
        </details>
      ))}
      {lesson.traps.length > 0 && (
        <details open id="lesson-traps" className="card lesson-section traps">
          <summary>
            <h2>Watch out</h2>
          </summary>
          <Facts lesson={lesson} facts={lesson.traps} images={false} />
        </details>
      )}
      <div className="card">
        <p>
          Now check it: the {s.questions} questions of this topic, with the answers you just read. A <span className="qref">Q</span> tag
          starts a round with just the questions of that fact.
        </p>
        <div className="actions">
          <a className="button primary" href={link('practice', topic.key, 'all')}>
            Practice this topic ({s.questions})
          </a>
          {next && (
            <a className="button" href={link('learn', next.key)}>
              Next lesson: {next.title} →
            </a>
          )}
        </div>
      </div>
    </>
  )
}

/** Facts with their question tags. Common-sense facts are grey; picture questions show the exam picture
 * (images=false in traps, whose pictures already show above). */
function Facts({ lesson, facts, images }: { lesson: Lesson; facts: Fact[]; images: boolean }) {
  return (
    <ul className="facts">
      {facts.map((f, i) => {
        const sense = isCommonSense(lesson, f)
        return (
          <li key={i} className={sense ? 'sense' : undefined}>
            {sense && <span className="tag">common sense</span>} <Rich text={f.text} />{' '}
            <a className="qref" href={link('practice', 'list', f.q.join(','))} title="Practice these exam questions">
              {f.q.map((id) => `Q${id}`).join(' ')}
            </a>
            {images &&
              f.q.map((id) => {
                const q = QUESTION_BY_ID.get(id)
                if (!q) throw new Error(`lesson fact refers to unknown question ${id}`)
                const src = imageUrl(q)
                return src && <img key={id} className="fact-img" src={src} alt={`Bild zu Frage ${id}`} loading="lazy" />
              })}
          </li>
        )
      })}
    </ul>
  )
}
