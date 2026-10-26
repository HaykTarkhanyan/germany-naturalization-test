import { Fragment, type ReactNode } from 'react'

/** Lets a line break after every "/": the catalog's paired forms ("Ministerpräsidentinnen/Ministerpräsidenten") are
 * otherwise one 35-letter word that pushed answer buttons off small phone screens. */
export function SoftBreaks({ text }: { text: string }): ReactNode {
  const parts = text.split('/')
  return parts.map((p, i) => (
    <Fragment key={i}>
      {p}
      {i < parts.length - 1 && (
        <>
          /<wbr />
        </>
      )}
    </Fragment>
  ))
}

/** Renders "a **b** c" with b in bold. */
export function Rich({ text }: { text: string }): ReactNode {
  return text.split('**').map((part, i) => (i % 2 === 1 ? <b key={i}>{part}</b> : part))
}
