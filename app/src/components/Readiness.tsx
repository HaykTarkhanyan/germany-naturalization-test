import { useMemo } from 'react'
import { useProgress } from '../lib/progress.ts'
import { readiness, statusById } from '../lib/stats.ts'

/** Pass chance today, from the questions known so far (last two answers right); the rest counts as guessed. */
export function Readiness() {
  const progress = useProgress()
  const r = useMemo(() => readiness(statusById(progress.answers)), [progress.answers])
  const known = r.knownGeneral + r.knownBayern
  return (
    <div className="card readiness">
      <div className="big">{(r.pass * 100).toFixed(r.pass < 0.1 && r.pass > 0 ? 1 : 0)}%</div>
      <div>
        <b>Chance to pass if the exam were today</b>
        <div className="muted">
          {known} of 310 known (Bayern {r.knownBayern}/10) · expected score {r.expected.toFixed(1)} of 33, 17 needed
        </div>
        <div className="muted small">
          Known = your last two answers to it were right. Everything else counts as a guess (25%).
        </div>
      </div>
    </div>
  )
}
