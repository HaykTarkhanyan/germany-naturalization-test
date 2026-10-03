import type { Counts } from '../lib/stats.ts'

/** Stacked bar known / learning / new, with the counts written next to it. */
export function StatusBar({ counts }: { counts: Counts }) {
  const total = counts.known + counts.learning + counts.new
  const pct = (n: number) => `${(100 * n) / total}%`
  return (
    <div className="status">
      <div className="bar" aria-hidden="true">
        <span className="seg known" style={{ width: pct(counts.known) }} />
        <span className="seg learning" style={{ width: pct(counts.learning) }} />
      </div>
      <span className="small">
        <b>{counts.known}</b> known · {counts.learning} learning · {counts.new} new
      </span>
    </div>
  )
}
