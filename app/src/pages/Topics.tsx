import { useMemo } from 'react'
import { ReadButton } from '../components/ReadButton.tsx'
import { StatusBar } from '../components/StatusBar.tsx'
import { MODULES, TOPICS, type Topic } from '../lib/data.ts'
import { useProgress } from '../lib/progress.ts'
import { link } from '../lib/router.ts'
import { countStatuses, statusById, type Status } from '../lib/stats.ts'

export function Topics() {
  const progress = useProgress()
  const statuses = useMemo(() => statusById(progress.answers), [progress.answers])
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
      </div>
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
