import { TOPIC_BY_KEY } from '../lib/data.ts'
import { factsFor } from '../lib/lessons.ts'
import { link } from '../lib/router.ts'
import { useSettings } from '../lib/settings.ts'
import { Rich } from './Text.tsx'

const LABELS = { en: { trap: 'Watch out: ', lesson: 'Lesson' }, ru: { trap: 'Осторожно: ', lesson: 'Урок' } } as const

/** The lesson facts behind a question's answer, shown after answering it (practice, exam review), in the
 * explanation language. */
export function Why({ id }: { id: number }) {
  const { videoLang: lang } = useSettings()
  const facts = factsFor(id, lang)
  const topic = facts[0].topic
  return (
    <div className="why" lang={lang}>
      {facts.map((f, i) => (
        <p key={i}>
          {f.trap && <b>{LABELS[lang].trap}</b>}
          <Rich text={f.text} />
        </p>
      ))}
      <a href={link('learn', topic)}>
        {LABELS[lang].lesson}: {TOPIC_BY_KEY.get(topic)?.title ?? topic}
      </a>
    </div>
  )
}
