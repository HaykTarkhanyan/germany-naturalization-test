# Reused answer buttons kept the focus, and Enter answered the next question with the old option

**Symptom:** In the mock exam, clicking option A with the mouse and pressing Enter to go on silently answered the
*next* question with A too. Measured on the live site (stored answers, 0 = A, 2 = C, null = unanswered): after
click A + Enter `[0, 0, null]`; after key 3 + Enter `[0, 2, 0]`. In practice, a second Enter on an unanswered
question answered it with the focused option and logged it as wrong (2 answers logged instead of 1).

**Cause:** `QuestionCard` keyed its option buttons by position (`key={i}`), so React reused the same four DOM buttons
for every question and the clicked button kept the keyboard focus. Enter on a focused button is a click, so after
the page's own Enter handler moved on, the browser "clicked" that button again, now on the new question. Practice
called `preventDefault()` for Enter only after an answer, the exam never did.

**Fix:** option buttons are keyed by question (`key={`${question.id}-${i}`}`), so every question gets new buttons
and no stale focus, and the exam's key handler calls `preventDefault()` for every key it handles. Re-tested:
`[0, null, null]` and `[0, 2, null]`; practice logs 1 answer; Tab to an option + Enter still answers in practice.

**Consequences:** Any list of clickable controls that is reused across "pages" of a flow (questions, cards) should
be keyed by the item, not the index. Key handlers that act on Enter/Space must `preventDefault()`, or the focused
element acts too.
