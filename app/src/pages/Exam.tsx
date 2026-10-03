import { useEffect, useState } from 'react'
import { QuestionCard } from '../components/QuestionCard.tsx'
import { QUESTION_BY_ID } from '../lib/data.ts'
import { EXAM } from '../lib/exam.ts'
import { correctIndices, finishExam, formatClock, newExam, remainingMs } from '../lib/examFlow.ts'
import { getProgress, updateProgress, useProgress, type ActiveExam, type ExamResult } from '../lib/progress.ts'
import { go, link } from '../lib/router.ts'

export function ExamPage({ resultId }: { resultId: string | null }) {
  const progress = useProgress()
  if (resultId !== null) {
    const result = progress.exams.find((e) => e.id === resultId)
    if (!result) {
      return (
        <div className="card error">
          <p>No finished exam with id {resultId} in this browser.</p>
          <a href={link('exam')}>Back to the exam page</a>
        </div>
      )
    }
    return <ExamResultView result={result} />
  }
  if (progress.activeExam) return <RunningExam exam={progress.activeExam} />
  return <ExamStart exams={progress.exams} />
}

function ExamStart({ exams }: { exams: ExamResult[] }) {
  const start = () => updateProgress((p) => ({ ...p, activeExam: newExam() }))
  return (
    <>
      <div className="card">
        <h1>Mock exam</h1>
        <ul>
          <li>
            {EXAM.questions} questions: {EXAM.general.draw} of the 300 general ones and {EXAM.bayern.draw} of the 10 Bayern ones, at
            random
          </li>
          <li>{EXAM.minutes} minutes; the exam ends by itself when the time is up</li>
          <li>{EXAM.passMark} correct answers pass; you see the answers only at the end</li>
          <li>You can leave and come back; the exam keeps running in this browser</li>
        </ul>
        <button type="button" className="primary" onClick={start}>
          Start the exam
        </button>
      </div>
      {exams.length > 0 && (
        <div className="card">
          <h2>Your exams</h2>
          <ExamHistory exams={exams} />
        </div>
      )}
    </>
  )
}

export function ExamHistory({ exams }: { exams: ExamResult[] }) {
  return (
    <table>
      <colgroup>
        <col style={{ width: '42%' }} />
        <col style={{ width: '18%' }} />
        <col style={{ width: '20%' }} />
        <col style={{ width: '20%' }} />
      </colgroup>
      <thead>
        <tr>
          <th>Date</th>
          <th className="num">Score</th>
          <th>Result</th>
          <th className="num">Time</th>
        </tr>
      </thead>
      <tbody>
        {[...exams].reverse().map((e) => (
          <tr key={e.id}>
            <td>
              <a href={link('exam', 'result', e.id)}>{new Date(e.finishedAt).toLocaleString()}</a>
            </td>
            <td className="num">{e.score} / 33</td>
            <td className={e.passed ? 'ok-text' : 'bad-text'}>{e.passed ? 'passed' : 'not passed'}</td>
            <td className="num">{formatClock(e.finishedAt - e.startedAt)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function submit(id: string, timedOut: boolean): void {
  const active = getProgress().activeExam
  if (!active || active.id !== id) return // already finished (e.g. the timer and the button at once)
  const { result, logged } = finishExam(active, Date.now(), timedOut)
  updateProgress((p) => ({ ...p, activeExam: null, exams: [...p.exams, result], answers: [...p.answers, ...logged] }))
  go('exam', 'result', id)
}

function RunningExam({ exam }: { exam: ActiveExam }) {
  const [index, setIndex] = useState(0)
  const [now, setNow] = useState(() => Date.now())
  const left = remainingMs(exam, now)
  const answered = exam.answers.filter((a) => a !== null).length
  const question = QUESTION_BY_ID.get(exam.questionIds[index])
  if (!question) throw new Error(`exam contains unknown question ${exam.questionIds[index]}`)

  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(t)
  }, [])

  useEffect(() => {
    if (left <= 0) submit(exam.id, true)
  }, [left, exam.id])

  function answer(i: number) {
    updateProgress((p) =>
      p.activeExam && p.activeExam.id === exam.id
        ? { ...p, activeExam: { ...p.activeExam, answers: p.activeExam.answers.map((a, k) => (k === index ? i : a)) } }
        : p,
    )
  }

  function move(delta: number) {
    setIndex((i) => Math.min(EXAM.questions - 1, Math.max(0, i + delta)))
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.ctrlKey || e.metaKey || e.altKey) return
      const k = e.key.toLowerCase()
      const idx = ['1', '2', '3', '4'].indexOf(k) >= 0 ? Number(k) - 1 : ['a', 'b', 'c', 'd'].indexOf(k)
      if (idx >= 0) answer(idx)
      else if (k === 'arrowright' || k === 'enter') move(1)
      else if (k === 'arrowleft') move(-1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  function onSubmit() {
    const open = EXAM.questions - answered
    if (open > 0 && !window.confirm(`${open} question${open === 1 ? ' is' : 's are'} not answered yet. Submit anyway?`)) return
    submit(exam.id, false)
  }

  function onCancel() {
    if (window.confirm('Cancel this exam? Its answers are thrown away and it does not count.')) {
      updateProgress((p) => ({ ...p, activeExam: null }))
    }
  }

  return (
    <>
      <div className="exam-bar">
        <span className={left < 5 * 60_000 ? 'bad-text' : ''}>
          <b>{formatClock(left)}</b> left
        </span>
        <span>
          {answered} / {EXAM.questions} answered
        </span>
        <button type="button" className="primary" onClick={onSubmit}>
          Submit
        </button>
      </div>
      <div className="navigator">
        {exam.questionIds.map((_, i) => (
          <button
            key={i}
            type="button"
            className={[exam.answers[i] !== null ? 'answered' : '', i === index ? 'current' : ''].join(' ')}
            onClick={() => setIndex(i)}
          >
            {i + 1}
          </button>
        ))}
      </div>
      <QuestionCard
        question={question}
        chosen={exam.answers[index]}
        reveal={false}
        onChoose={answer}
        label={`Question ${index + 1} of ${EXAM.questions}`}
      />
      <div className="actions spread">
        <button type="button" onClick={() => move(-1)} disabled={index === 0}>
          ← Previous
        </button>
        <button type="button" onClick={() => move(1)} disabled={index === EXAM.questions - 1}>
          Next →
        </button>
      </div>
      <p className="muted small hint">
        Keys: 1-4 or A-D to answer, ←/→ to move. <button type="button" className="linklike" onClick={onCancel}>Cancel this exam</button>
      </p>
    </>
  )
}

function ExamResultView({ result }: { result: ExamResult }) {
  const correct = correctIndices(result.questionIds)
  const rows = result.questionIds.map((id, i) => ({ id, i, chosen: result.answers[i], right: result.answers[i] === correct[i] }))
  const wrong = rows.filter((r) => !r.right)
  const right = rows.filter((r) => r.right)
  const card = (r: (typeof rows)[number]) => {
    const q = QUESTION_BY_ID.get(r.id)
    if (!q) throw new Error(`exam contains unknown question ${r.id}`)
    return (
      <QuestionCard
        key={r.id}
        question={q}
        chosen={r.chosen}
        reveal
        label={`Question ${r.i + 1}${r.chosen === null ? ' · not answered' : ''}`}
      />
    )
  }
  return (
    <>
      <div className={`card result ${result.passed ? 'ok' : 'bad'}`}>
        <div className="big">
          {result.score} / 33
        </div>
        <div>
          <b>{result.passed ? 'Passed' : 'Not passed'}</b> (17 needed)
          <div className="muted">
            {new Date(result.finishedAt).toLocaleString()} · took {formatClock(result.finishedAt - result.startedAt)}
            {result.timedOut ? ' · time ran out' : ''}
          </div>
        </div>
      </div>
      <div className="actions">
        {wrong.length > 0 && (
          <a className="button primary" href={link('practice', 'list', wrong.map((r) => r.id).join(','))}>
            Practice the {wrong.length} mistakes
          </a>
        )}
        <a className="button" href={link('exam')}>
          Exam page
        </a>
      </div>
      {wrong.length > 0 && (
        <details open className="card plain">
          <summary>
            <b>Wrong or not answered ({wrong.length})</b>
          </summary>
          {wrong.map(card)}
        </details>
      )}
      <details className="card plain">
        <summary>
          <b>Right ({right.length})</b>
        </summary>
        {right.map(card)}
      </details>
    </>
  )
}
