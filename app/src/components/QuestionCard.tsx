import { imageUrl, TOPIC_OF_QUESTION, type Question } from '../lib/data.ts'

type Props = {
  question: Question
  chosen: number | null
  /** Show right/wrong colouring (practice after answering, exam review). */
  reveal: boolean
  onChoose?: (index: number) => void
  label?: string
}

export function QuestionCard({ question, chosen, reveal, onChoose, label }: Props) {
  const img = imageUrl(question)
  const topic = TOPIC_OF_QUESTION.get(question.id)
  return (
    <div className="card question">
      <div className="question-meta">
        {label && <span>{label}</span>}
        <span>
          Frage {question.id}
          {question.section === 'Bayern' ? ' (Bayern)' : ''}
          {topic ? ` · ${topic.title}` : ''}
        </span>
      </div>
      <p className="question-text">{question.question}</p>
      {img && <img className="question-img" src={img} alt={`Bild zu Frage ${question.id}`} />}
      <div className="options">
        {question.options.map((opt, i) => {
          const classes = ['option']
          if (chosen === i) classes.push('chosen')
          if (reveal && i === question.answer_index) classes.push('correct')
          if (reveal && chosen === i && i !== question.answer_index) classes.push('wrong')
          return (
            <button
              key={i}
              type="button"
              className={classes.join(' ')}
              disabled={!onChoose}
              onClick={() => onChoose?.(i)}
            >
              <span className="option-key">{'ABCD'[i]}</span>
              <span>{opt}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
