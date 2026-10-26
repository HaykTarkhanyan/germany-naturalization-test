import { useMemo } from 'react'
import { ReadButton } from '../components/ReadButton.tsx'
import { Readiness } from '../components/Readiness.tsx'
import { TOPICS } from '../lib/data.ts'
import { EXAM } from '../lib/exam.ts'
import { useProgress } from '../lib/progress.ts'
import { link } from '../lib/router.ts'
import { countStatuses, lastWrong, statusById } from '../lib/stats.ts'

// Bayern first: each Bayern question is three times as likely to be on the sheet (3 of 10 vs 30 of 300).
const STUDY_ORDER = [...TOPICS.filter((t) => t.module === 'bayern'), ...TOPICS.filter((t) => t.module !== 'bayern')]

/** Calendar days in local time: an exam at 23:00 is "yesterday" the next morning, not "today". */
function daysAgo(t: number): string {
  const day = (ms: number) => {
    const d = new Date(ms)
    return Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86_400_000
  }
  const d = day(Date.now()) - day(t)
  return d <= 0 ? 'today' : d === 1 ? 'yesterday' : `${d} days ago`
}

export function Home() {
  const progress = useProgress()
  const statuses = useMemo(() => statusById(progress.answers), [progress.answers])
  const mistakes = useMemo(() => lastWrong(progress.answers), [progress.answers])
  const lastExam = progress.exams.at(-1)
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
      {mistakes.length > 0 && (
        <div className="card">
          <h2>My mistakes</h2>
          <p>
            {mistakes.length} question{mistakes.length === 1 ? '' : 's'} you got wrong the last time you answered{' '}
            {mistakes.length === 1 ? 'it' : 'them'}, from every topic and the mock exams.
          </p>
          <a className="button primary" href={link('practice', 'mistakes', 'all')}>
            Repeat my mistakes ({mistakes.length})
          </a>
        </div>
      )}
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
        {lastExam && (
          <p>
            Last one:{' '}
            <a href={link('exam', 'result', lastExam.id)}>
              {lastExam.score} / {EXAM.questions}, {lastExam.passed ? 'passed' : 'not passed'}
            </a>{' '}
            · {daysAgo(lastExam.finishedAt)} · {progress.exams.length} so far
          </p>
        )}
        <a className="button" href={link('exam')}>
          {progress.activeExam ? 'Continue the exam' : 'Start a mock exam'}
        </a>
      </div>
    </>
  )
}
