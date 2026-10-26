import { useMemo, useState } from 'react'
import { ReadButton } from '../components/ReadButton.tsx'
import { StatusBar } from '../components/StatusBar.tsx'
import { SoftBreaks } from '../components/Text.tsx'
import { english, imageUrl, MODULES, TOPIC_OF_QUESTION, TOPICS, type Question, type Topic } from '../lib/data.ts'
import { useProgress } from '../lib/progress.ts'
import { link } from '../lib/router.ts'
import { searchQuestions } from '../lib/search.ts'
import { useSettings } from '../lib/settings.ts'
import { countStatuses, lastWrong, statusById, type Status } from '../lib/stats.ts'

const SHOWN = 20         // search hits listed
const MAX_PRACTICE = 40  // as on the Words page

export function Topics() {
  const progress = useProgress()
  const statuses = useMemo(() => statusById(progress.answers), [progress.answers])
  const mistakes = useMemo(() => lastWrong(progress.answers), [progress.answers])
  return (
    <>
      <div className="card">
        <h1>Topics</h1>
        <p className="muted">
          310 questions in 24 topics. Within a topic, related questions come one after another, so similar answers are learned side by
          side.
        </p>
        <div className="toc">
          {MODULES.map((m) => (
            <button
              key={m.key}
              type="button"
              className="linklike"
              onClick={() => document.getElementById(`module-${m.key}`)?.scrollIntoView({ behavior: 'smooth' })}
            >
              {m.title}
            </button>
          ))}
        </div>
        {mistakes.length > 0 && (
          <div className="actions">
            <a className="button primary" href={link('practice', 'mistakes', 'all')}>
              Repeat my mistakes ({mistakes.length})
            </a>
          </div>
        )}
      </div>
      <QuestionSearch statuses={statuses} />
      {MODULES.map((m) => {
        const topics = TOPICS.filter((t) => t.module === m.key)
        const ids = topics.flatMap((t) => t.questions)
        return (
          <details open key={m.key} id={`module-${m.key}`} className="card module">
            <summary>
              <span className="module-title">{m.title}</span>{' '}
              <span className="muted small">
                {m.title_en} · {ids.length} questions
              </span>
              <StatusBar counts={countStatuses(ids, statuses)} />
            </summary>
            {topics.map((t) => (
              <TopicRow key={t.key} topic={t} statuses={statuses} />
            ))}
          </details>
        )
      })}
    </>
  )
}

function TopicRow({ topic, statuses }: { topic: Topic; statuses: ReadonlyMap<number, Status> }) {
  const counts = countStatuses(topic.questions, statuses)
  const open = topic.questions.length - counts.known
  return (
    <div className="topic">
      <div>
        <b>{topic.title}</b>{' '}
        <span className="muted small">
          {topic.title_en} · {topic.questions.length} questions
        </span>
      </div>
      <StatusBar counts={counts} />
      <div className="actions">
        {open > 0 && (
          <a className="button primary" href={link('practice', topic.key, 'open')}>
            Not known yet ({open})
          </a>
        )}
        <a className="button" href={link('practice', topic.key, 'all')}>
          All {topic.questions.length}
        </a>
        <ReadButton topicKey={topic.key} />
      </div>
    </div>
  )
}

const STATUS_LABEL: Record<Status, string> = { new: 'not answered yet', learning: 'learning', known: 'known' }

/** Find any question by number or words, with its answer, your status and a practice link. */
function QuestionSearch({ statuses }: { statuses: ReadonlyMap<number, Status> }) {
  const [query, setQuery] = useState('')
  const hits = useMemo(() => searchQuestions(query), [query])
  return (
    <div className="card">
      <h2>Find a question</h2>
      <div className="word-controls">
        <input
          type="search"
          placeholder="Number or words, German or English"
          aria-label="Find a question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {query.trim() !== '' && (
        <>
          <p className="muted small">
            {hits.length === 0
              ? 'No question matches. Umlauts are optional (ubersetzer finds Übersetzer).'
              : `${hits.length} question${hits.length === 1 ? '' : 's'}${hits.length > SHOWN ? `, showing the first ${SHOWN}` : ''}`}
          </p>
          <ul className="answers">
            {hits.slice(0, SHOWN).map((q) => (
              <SearchHit key={q.id} q={q} status={statuses.get(q.id) ?? 'new'} />
            ))}
          </ul>
          {hits.length > 1 && hits.length <= MAX_PRACTICE && (
            <div className="actions">
              <a className="button" href={link('practice', 'list', hits.map((q) => q.id).join(','))}>
                Practice these {hits.length}
              </a>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function SearchHit({ q, status }: { q: Question; status: Status }) {
  const { showEnglish } = useSettings()
  const en = english(q)
  const topic = TOPIC_OF_QUESTION.get(q.id)
  const img = imageUrl(q)
  const answerEn = en.options[q.answer_index]
  const answer = q.options[q.answer_index]
  return (
    <li>
      <span className="muted small">
        Frage {q.id}
        {q.section === 'Bayern' ? ' (Bayern)' : ''} · {topic?.title ?? ''} · <span className={`status-${status}`}>{STATUS_LABEL[status]}</span>
      </span>
      <span className="answer-q">
        <SoftBreaks text={q.question} />
      </span>
      {showEnglish && (
        <span className="en">
          <SoftBreaks text={en.question} />
        </span>
      )}
      {img && <img className="fact-img" src={img} alt={`Bild zu Frage ${q.id}`} loading="lazy" />}
      <span className="answer-a">
        ✓ <SoftBreaks text={answer} />
        {showEnglish && answerEn !== answer && !/^(Image )?\d$/.test(answerEn) && (
          <span className="en">
            <SoftBreaks text={answerEn} />
          </span>
        )}
      </span>
      <span className="small">
        <a href={link('practice', 'list', String(q.id))}>Practice it</a>
        {topic && (
          <>
            {' · '}
            <a href={link('learn', topic.key)}>Lesson</a>
          </>
        )}
      </span>
    </li>
  )
}
