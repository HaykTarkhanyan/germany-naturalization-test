import { TOPIC_BY_KEY } from '../lib/data.ts'
import { factsFor } from '../lib/lessons.ts'
import { link } from '../lib/router.ts'
import { Rich } from './Text.tsx'

/** The lesson facts behind a question's answer, shown after answering it (practice, exam review). */
export function Why({ id }: { id: number }) {
  const facts = factsFor(id)
  const topic = facts[0].topic
  return (
    <div className="why">
      {facts.map((f, i) => (
        <p key={i}>
          {f.trap && <b>Watch out: </b>}
          <Rich text={f.text} />
        </p>
      ))}
      <a href={link('learn', topic)}>Lesson: {TOPIC_BY_KEY.get(topic)?.title ?? topic}</a>
    </div>
  )
}
