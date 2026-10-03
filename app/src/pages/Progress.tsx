import { useMemo, useState, type ChangeEvent } from 'react'
import { Readiness } from '../components/Readiness.tsx'
import { MODULES, TOPICS } from '../lib/data.ts'
import {
  downloadText,
  emptyProgress,
  exportFileName,
  parseProgress,
  ProgressError,
  replaceProgress,
  useProgress,
} from '../lib/progress.ts'
import { link } from '../lib/router.ts'
import { countStatuses, statusById } from '../lib/stats.ts'
import { ExamHistory } from './Exam.tsx'

export function ProgressPage() {
  const progress = useProgress()
  const statuses = useMemo(() => statusById(progress.answers), [progress.answers])
  const [importMessage, setImportMessage] = useState<{ ok: boolean; text: string } | null>(null)

  async function onImport(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    let incoming
    try {
      incoming = parseProgress(await file.text(), `"${file.name}"`)
    } catch (err) {
      if (!(err instanceof ProgressError)) throw err
      setImportMessage({ ok: false, text: err.message })
      return
    }
    const question =
      `Replace the progress in this browser (${progress.answers.length} answers, ${progress.exams.length} exams) ` +
      `with "${file.name}" (${incoming.answers.length} answers, ${incoming.exams.length} exams)?`
    if (!window.confirm(question)) return
    replaceProgress(incoming)
    setImportMessage({ ok: true, text: `Imported "${file.name}".` })
  }

  function onReset() {
    if (window.confirm(`Delete all progress in this browser (${progress.answers.length} answers, ${progress.exams.length} exams)?`)) {
      replaceProgress(emptyProgress())
    }
  }

  return (
    <>
      <Readiness />
      <div className="card">
        <h2>By topic</h2>
        <table>
          <colgroup>
            <col style={{ width: '46%' }} />
            <col style={{ width: '12%' }} />
            <col style={{ width: '12%' }} />
            <col style={{ width: '15%' }} />
            <col style={{ width: '15%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>Topic</th>
              <th className="num">Known</th>
              <th className="num">Learning</th>
              <th className="num">New</th>
              <th className="num">Known %</th>
            </tr>
          </thead>
          {MODULES.map((m) => (
            <tbody key={m.key}>
              <tr className="group">
                <td colSpan={5}>{m.title}</td>
              </tr>
              {TOPICS.filter((t) => t.module === m.key).map((t) => {
                const c = countStatuses(t.questions, statuses)
                return (
                  <tr key={t.key}>
                    <td>
                      <a href={link('practice', t.key, 'open')}>{t.title}</a>
                    </td>
                    <td className="num">{c.known}</td>
                    <td className="num">{c.learning}</td>
                    <td className="num">{c.new}</td>
                    <td className="num">{Math.round((100 * c.known) / t.questions.length)}%</td>
                  </tr>
                )
              })}
            </tbody>
          ))}
        </table>
      </div>
      <div className="card">
        <h2>Mock exams</h2>
        {progress.exams.length > 0 ? <ExamHistory exams={progress.exams} /> : <p className="muted">No mock exams yet.</p>}
      </div>
      <div className="card">
        <h2>Your data</h2>
        <p className="muted">
          Progress is saved only in this browser ({progress.answers.length} answers, {progress.exams.length} exams). Export it to keep a
          copy or to move it to another device, then import it there.
        </p>
        <div className="actions">
          <button type="button" onClick={() => downloadText(JSON.stringify(progress), exportFileName())}>
            Export progress
          </button>
          <label className="button">
            Import progress
            <input type="file" accept=".json,application/json" onChange={onImport} hidden />
          </label>
          <button type="button" className="danger" onClick={onReset}>
            Reset
          </button>
        </div>
        {importMessage && <p className={importMessage.ok ? 'ok-text' : 'bad-text'}>{importMessage.text}</p>}
      </div>
    </>
  )
}
