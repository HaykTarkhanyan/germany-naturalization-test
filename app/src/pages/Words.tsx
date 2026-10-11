import { useMemo, useState } from 'react'
import { link } from '../lib/router.ts'
import { ABBREVIATIONS_EXCLUDED, KIND_LABELS, NAMES_EXCLUDED, WORDS, wordsForShare, type Word, type WordKind } from '../lib/vocabulary.ts'

const PAGE = 150
const MAX_PRACTICE = 40 // words like "der" are in most questions; a practice round of all of them makes no sense
// only the word types that occur, in KIND_LABELS order
const KIND_FILTERS: [string, string][] = [
  ['all', 'All words'],
  ...(Object.entries(KIND_LABELS) as [WordKind, string][]).filter(([k]) => WORDS.some((w) => w.kind === k)),
]
const CORE = WORDS.filter((w) => w.core).length
const HALF = wordsForShare(0.5)
const MOST = wordsForShare(0.8)

/** "die Wahl" with the article coloured by gender (der blue, die red, das green). */
function German({ de }: { de: string }) {
  const m = de.match(/^(der|die|das) (.+)$/)
  if (!m) return <b>{de}</b>
  return (
    <>
      <span className={`article ${m[1]}`}>{m[1]}</span> <b>{m[2]}</b>
    </>
  )
}

function matches(w: Word, q: string): boolean {
  // the article is left out, otherwise "der" would match every masculine noun
  const de = w.de.replace(/^(der|die|das) /, '').toLowerCase()
  return de.includes(q) || w.en.toLowerCase().includes(q) || w.forms.some((f) => f.toLowerCase().includes(q))
}

export function Words() {
  const [query, setQuery] = useState('')
  const [kind, setKind] = useState('all')
  const [coreOnly, setCoreOnly] = useState(false)
  const [alphabetical, setAlphabetical] = useState(false)
  const [shown, setShown] = useState(PAGE)

  const list = useMemo(() => {
    const q = query.trim().toLowerCase()
    const out = WORDS.filter(
      (w) => (kind === 'all' || w.kind === (kind as WordKind)) && (!coreOnly || w.core) && (q === '' || matches(w, q)),
    )
    if (alphabetical) out.sort((a, b) => a.lemma.localeCompare(b.lemma, 'de'))
    return out
  }, [query, kind, coreOnly, alphabetical])

  return (
    <>
      <div className="card">
        <h1>Words</h1>
        <p>
          <b>{WORDS.length.toLocaleString('en')}</b> German words appear in the 310 questions and their options (dictionary forms: "wählt" and
          "gewählt" count once as "wählen"). <b>{CORE}</b> of them are in a question or a correct answer. The {HALF} most frequent words make up
          half of all the text, the top {MOST} make up 80%.
        </p>
        <p className="muted small">
          Not counted: {NAMES_EXCLUDED} names and places, and {ABBREVIATIONS_EXCLUDED.length} abbreviations ({ABBREVIATIONS_EXCLUDED.join(', ')}).
          Female forms (Bürgerin) are listed under the base word (Bürger). English meanings are machine translations, checked by spot
          tests.
        </p>
        <div className="word-controls">
          <input
            type="search"
            placeholder="Search German or English"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setShown(PAGE)
            }}
          />
          <select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value)
              setShown(PAGE)
            }}
          >
            {KIND_FILTERS.map(([k, label]) => (
              <option key={k} value={k}>
                {label}
              </option>
            ))}
          </select>
          <label>
            <input
              type="checkbox"
              checked={coreOnly}
              onChange={(e) => {
                setCoreOnly(e.target.checked)
                setShown(PAGE)
              }}
            />{' '}
            Only questions and correct answers
          </label>
          <label>
            <input type="checkbox" checked={alphabetical} onChange={(e) => setAlphabetical(e.target.checked)} /> A-Z
          </label>
        </div>
      </div>
      <div className="card">
        <p className="muted small">
          {list.length.toLocaleString('en')} words{list.length > shown ? `, showing the first ${shown}` : ''}. "Times" = how often the word appears in
          the catalog.
        </p>
        <table className="words-table">
          <colgroup>
            <col style={{ width: '36%' }} />
            <col style={{ width: '38%' }} />
            <col style={{ width: '10%' }} />
            <col style={{ width: '16%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>German</th>
              <th>English</th>
              <th className="num">Times</th>
              <th className="num">Practice</th>
            </tr>
          </thead>
          <tbody>
            {list.slice(0, shown).map((w) => (
              <tr key={w.key}>
                <td>
                  <German de={w.de} />
                </td>
                <td>{w.en}</td>
                <td className="num">{w.count}</td>
                <td className="num">
                  {w.questions.length <= MAX_PRACTICE ? (
                    <a href={link('practice', 'list', w.questions.join(','))} title="Practice the questions with this word">
                      {w.questions.length} Q
                    </a>
                  ) : (
                    <span className="muted" title="In too many questions for a practice round">
                      {w.questions.length} Q
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length > shown && (
          <div className="actions">
            <button type="button" onClick={() => setShown((s) => s + PAGE)}>
              Show {Math.min(PAGE, list.length - shown)} more
            </button>
          </div>
        )}
      </div>
    </>
  )
}
