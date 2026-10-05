import { LESSON_BY_TOPIC, readingMinutes } from '../lib/lessons.ts'
import { link } from '../lib/router.ts'

/** Link to a topic's lesson, with its reading time. */
export function ReadButton({ topicKey }: { topicKey: string }) {
  const lesson = LESSON_BY_TOPIC.get(topicKey)
  if (!lesson) throw new Error(`no lesson for topic ${topicKey}`)
  return (
    <a className="button" href={link('learn', topicKey)}>
      Read the lesson ({readingMinutes(lesson)} min)
    </a>
  )
}
