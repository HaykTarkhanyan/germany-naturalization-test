import { useEffect, useRef } from 'react'
import { emptyProgress, downloadText, replaceProgress, useLoadError, type ProgressError } from './lib/progress.ts'
import { link, useRoute } from './lib/router.ts'
import { updateSettings, useSettings } from './lib/settings.ts'
import { ExamPage, finishExpiredExam } from './pages/Exam.tsx'
import { Home } from './pages/Home.tsx'
import { Learn, LessonPage } from './pages/Learn.tsx'
import { Practice } from './pages/Practice.tsx'
import { ProgressPage } from './pages/Progress.tsx'
import { Topics } from './pages/Topics.tsx'
import { VideosPage, VideoTextPage } from './pages/VideoText.tsx'
import { Words } from './pages/Words.tsx'

const NAV: [string, string][] = [
  ['', 'Home'],
  ['learn', 'Learn'],
  ['videos', 'Videos'],
  ['words', 'Words'],
  ['topics', 'Topics'],
  ['exam', 'Exam'],
  ['progress', 'Progress'],
]

export function App() {
  const route = useRoute()
  const loadError = useLoadError()
  const { showEnglish, videoLang } = useSettings()
  const page = route[0] ?? ''
  const path = route.join('/')
  useEffect(() => {
    if (!loadError) finishExpiredExam()
  }, [path, loadError])
  // On a phone the menu is one row that scrolls sideways: keep the current page's item in view (sideways only, so the
  // page itself never jumps).
  const navRef = useRef<HTMLElement>(null)
  useEffect(() => {
    const nav = navRef.current
    const active = nav?.querySelector<HTMLElement>('a.active')
    if (nav && active) nav.scrollLeft = active.offsetLeft - (nav.clientWidth - active.offsetWidth) / 2
  }, [page])
  return (
    <>
      <header>
        <a className="brand" href={link()}>
          Einbürgerungstest
        </a>
        <nav ref={navRef}>
          {NAV.map(([key, label]) => (
            <a key={key} href={link(...(key ? [key] : []))} className={page === key || (key === 'topics' && page === 'practice') || (key === 'videos' && page === 'read') ? 'active' : ''}>
              {label}
            </a>
          ))}
        </nav>
        <div className="toggles">
          <button
            type="button"
            className={`toggle ${showEnglish ? 'on' : ''}`}
            aria-pressed={showEnglish}
            title="Show the English translation under every question and answer"
            onClick={() => updateSettings({ showEnglish: !showEnglish })}
          >
            English {showEnglish ? 'on' : 'off'}
          </button>
          <button
            type="button"
            className="toggle on"
            title="Language of the lessons, the explanations after each answer, and the videos"
            onClick={() => updateSettings({ videoLang: videoLang === 'en' ? 'ru' : 'en' })}
          >
            {/* one span: buttons are flex boxes, and a gap between the parts read "Explain : EN" */}
            <span>
              <span className="long-label">Explanations</span>
              <span className="short-label">Explain</span>: {videoLang === 'en' ? 'EN' : 'RU'}
            </span>
          </button>
        </div>
      </header>
      <main>{loadError ? <Recovery error={loadError} /> : <Page route={route} />}</main>
    </>
  )
}

function Page({ route }: { route: string[] }) {
  switch (route[0] ?? '') {
    case '':
      return <Home />
    case 'learn':
      return route[1] ? <LessonPage key={route[1]} topicKey={route[1]} /> : <Learn />
    case 'videos':
      return <VideosPage />
    case 'read':
      return <VideoTextPage key={route[1] ?? ''} slug={route[1] ?? ''} />
    case 'words':
      return <Words />
    case 'topics':
      return <Topics />
    case 'practice':
      return <Practice key={route.join('/')} source={route[1] ?? ''} arg={route[2] ?? 'all'} />
    case 'exam':
      return <ExamPage key={route.join('/')} resultId={route[1] === 'result' ? (route[2] ?? null) : null} />
    case 'progress':
      return <ProgressPage />
    default:
      return (
        <div className="card">
          <p>There is no page "{route.join('/')}".</p>
          <a href={link()}>Go to Home</a>
        </div>
      )
  }
}

/** Stored progress could not be read. Never replaced silently: download it first, then reset. */
function Recovery({ error }: { error: ProgressError }) {
  return (
    <div className="card error">
      <h2>Your saved progress could not be loaded</h2>
      <p>{error.message}</p>
      <p>Download the stored data first if you want to keep it, then start fresh.</p>
      <div className="actions">
        {error.raw !== null && (
          <button type="button" onClick={() => downloadText(error.raw ?? '', 'einbuergerungstest-progress-broken.json')}>
            Download the stored data
          </button>
        )}
        <button
          type="button"
          className="danger"
          onClick={() => {
            if (window.confirm('Delete the stored progress and start with empty progress?')) replaceProgress(emptyProgress())
          }}
        >
          Start with empty progress
        </button>
      </div>
    </div>
  )
}
