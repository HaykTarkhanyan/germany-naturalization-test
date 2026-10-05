import { useEffect, useState } from 'react'
import { QuestionCard } from '../components/QuestionCard.tsx'
import { ReadButton } from '../components/ReadButton.tsx'
import { english, QUESTION_BY_ID, TOPIC_BY_KEY, TOPICS, type Question } from '../lib/data.ts'
import { getProgress, recordAnswer } from '../lib/progress.ts'
import { link } from '../lib/router.ts'
import { useSettings } from '../lib/settings.ts'
import { statusById } from '../lib/stats.ts'

type Session = { title: string; ids: number[]; topicKey: string | null }

/**
 * source = a topic key with arg "all" or "open" (not known yet), or "list" with arg = comma-separated
 * question ids (e.g. the mistakes of a mock exam).
 */
function buildSession(source: string, arg: string): Session | string {
  if (source === 'list') {
    const ids = arg.split(',').map(Number)
    const bad = ids.filter((id) => !QUESTION_BY_ID.has(id))
    if (bad.length > 0 || ids.length === 0) return `"${arg}" is not a list of question numbers 1-310.`
    return { title: 'Selected questions', ids, topicKey: null }
  }
  const topic = TOPIC_BY_KEY.get(source)
  if (!topic) return `There is no topic "${source}".`
  if (arg === 'all') return { title: topic.title, ids: topic.questions, topicKey: topic.key }
  if (arg === 'open') {
    const statuses = statusById(getProgress().answers)
    return { title: `${topic.title} · not known yet`, ids: topic.questions.filter((id) => statuses.get(id) !== 'known'), topicKey: topic.key }
  }
  return `Unknown practice mode "${arg}" (use "all" or "open").`
}

function question(id: number): Question {
  const q = QUESTION_BY_ID.get(id)
  if (!q) throw new Error(`question ${id} does not exist`)
  return q
}

export function Practice({ source, arg }: { source: string; arg: string }) {
  const [session] = useState(() => buildSession(source, arg))
  const [queue, setQueue] = useState<number[]>(() => (typeof session === 'string' ? [] : session.ids))
  const [pos, setPos] = useState(0)
  const [chosen, setChosen] = useState<number | null>(null)
  const [results, setResults] = useState<{ id: number; correct: boolean }[]>([])
  const { showEnglish } = useSettings()

  const current = pos < queue.length ? question(queue[pos]) : null

  function choose(i: number) {
    if (current === null || chosen !== null) return
    const correct = i === current.answer_index
    setChosen(i)
    setResults((r) => [...r, { id: current.id, correct }])
    recordAnswer(current.id, i, correct, 'practice')
  }

  function next() {
    if (chosen === null) return
    setChosen(null)
    setPos((p) => p + 1)
  }

  function restart(ids: number[]) {
    setQueue(ids)
    setPos(0)
    setChosen(null)
    setResults([])
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.ctrlKey || e.metaKey || e.altKey) return
      const k = e.key.toLowerCase()
      const idx = ['1', '2', '3', '4'].indexOf(k) >= 0 ? Number(k) - 1 : ['a', 'b', 'c', 'd'].indexOf(k)
      if (idx >= 0 && chosen === null) {
        e.preventDefault()
        choose(idx)
      } else if ((k === 'enter' || k === ' ' || k === 'arrowright') && chosen !== null) {
        e.preventDefault()
        next()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  if (typeof session === 'string') {
    return (
      <div className="card error">
        <p>{session}</p>
        <a href={link('topics')}>Back to topics</a>
      </div>
    )
  }

  if (queue.length === 0) {
    return (
      <div className="card">
        <h2>{session.title}</h2>
        <p>Nothing left here: you know every question in this topic.</p>
        <div className="actions">
          {session.topicKey && (
            <a className="button" href={link('practice', session.topicKey, 'all')}>
              Practice all of them anyway
            </a>
          )}
          <a className="button" href={link('topics')}>
            Back to topics
          </a>
        </div>
      </div>
    )
  }

  if (current === null) {
    const missed = results.filter((r) => !r.correct).map((r) => r.id)
    const idx = session.topicKey ? TOPICS.findIndex((t) => t.key === session.topicKey) : -1
    const nextTopic = idx >= 0 && idx + 1 < TOPICS.length ? TOPICS[idx + 1] : null
    return (
      <div className="card">
        <h2>{session.title}: done</h2>
        <p className="big-line">
          {results.length - missed.length} of {results.length} right
        </p>
        {missed.length > 0 && (
          <ul className="missed">
            {missed.map((id) => {
              const q = question(id)
              return (
                <li key={id}>
                  <span className="muted">Frage {id}:</span> {q.question} <b>→ {q.answer}</b>
                  {showEnglish && (
                    <span className="en">
                      {english(q).question} → {english(q).options[q.answer_index]}
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
        )}
        <div className="actions">
          {missed.length > 0 && (
            <button type="button" className="primary" onClick={() => restart(missed)}>
              Practice the {missed.length} I missed
            </button>
          )}
          <button type="button" onClick={() => restart(queue)}>
            Again ({queue.length})
          </button>
          {session.topicKey && missed.length > 0 && <ReadButton topicKey={session.topicKey} />}
          {nextTopic && (
            <a className="button" href={link('practice', nextTopic.key, 'open')}>
              Next topic: {nextTopic.title}
            </a>
          )}
          <a className="button" href={link('topics')}>
            Topics
          </a>
        </div>
      </div>
    )
  }

  const right = chosen !== null && chosen === current.answer_index
  return (
    <>
      <div className="practice-head">
        <a href={link('topics')}>← Topics</a>
        <span>
          <b>{session.title}</b> · {pos + 1} / {queue.length}
        </span>
      </div>
      <div className="bar thin" aria-hidden="true">
        <span className="seg known" style={{ width: `${(100 * pos) / queue.length}%` }} />
      </div>
      <QuestionCard question={current} chosen={chosen} reveal={chosen !== null} onChoose={choose} />
      {chosen !== null && (
        <div className={`card feedback ${right ? 'ok' : 'bad'}`}>
          <span>
            {right ? 'Right.' : (
              <>
                Not quite. Right answer: <b>{'ABCD'[current.answer_index]}) {current.answer}</b>
                {showEnglish && english(current).options[current.answer_index] !== current.answer && (
                  <span className="en">{english(current).options[current.answer_index]}</span>
                )}
              </>
            )}
          </span>
          <button type="button" className="primary" onClick={next}>
            Next (Enter)
          </button>
        </div>
      )}
      <p className="muted small hint">Keys: 1-4 or A-D to answer, Enter for the next question.</p>
    </>
  )
}
