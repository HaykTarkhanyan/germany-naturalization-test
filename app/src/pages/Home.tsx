import { useMemo } from 'react'
import { Readiness } from '../components/Readiness.tsx'
import { TOPICS } from '../lib/data.ts'
import { EXAM } from '../lib/exam.ts'
import { useProgress } from '../lib/progress.ts'
import { link } from '../lib/router.ts'
import { countStatuses, statusById } from '../lib/stats.ts'
import { ReadButton } from './Topics.tsx'

// Bayern first: each Bayern question is three times as likely to be on the sheet (3 of 10 vs 30 of 300).
const STUDY_ORDER = [...TOPICS.filter((t) => t.module === 'bayern'), ...TOPICS.filter((t) => t.module !== 'bayern')]

export function Home() {
  const progress = useProgress()
  const statuses = useMemo(() => statusById(progress.answers), [progress.answers])
  const next = STUDY_ORDER.map((t) => ({ t, open: t.questions.length - countStatuses(t.questions, statuses).known })).find(
    (x) => x.open > 0,
  )
  return (
    <>
      {progress.activeExam && (
        <div className="card notice">
          You have a mock exam in progress. <a href={link('exam')}>Continue it</a>
        </div>
      )}
      <Readiness />
      <div className="card">
        <h2>Next up</h2>
        {next ? (
          <>
            <p>
              <b>{next.t.title}</b> <span className="muted">{next.t.title_en}</span> · {next.open} of {next.t.questions.length} not
              known yet
            </p>
            <div className="actions">
              <a className="button primary" href={link('practice', next.t.key, 'open')}>
                Practice them
              </a>
              <ReadButton topicKey={next.t.key} />
              <a className="button" href={link('topics')}>
                All topics
              </a>
            </div>
            {next.t.module === 'bayern' && (
              <p className="muted small">
                Bayern first: each Bayern question is three times as likely to be on your sheet as a general one (3 of 10 vs 30 of 300).
              </p>
            )}
          </>
        ) : (
          <p>You know all 310 questions. Take a mock exam to check.</p>
        )}
      </div>
      <div className="card">
        <h2>Mock exam</h2>
        <p className="muted">
          {EXAM.questions} questions ({EXAM.general.draw} general + {EXAM.bayern.draw} Bayern), {EXAM.minutes} minutes,{' '}
          {EXAM.passMark} correct to pass.
        </p>
        <a className="button" href={link('exam')}>
          {progress.activeExam ? 'Continue the exam' : 'Start a mock exam'}
        </a>
      </div>
    </>
  )
}
