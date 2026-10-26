# Paired forms with "/" do not wrap and pushed answer buttons off small phone screens

**Symptom:** On a 375 px phone, Q128 option D ("Ministerpräsidentinnen/Ministerpräsidenten.") was cut off and the
whole page scrolled sideways. A Playwright sweep over all 310 questions found 5 overflowing at 375 px (37, 88, 128,
299, 309; Q128 by 64 px) and 8 at 340 px, about the width of a card nested in the exam review (plus 99, 252, 310).
Two of them (309, 310) are Bayern questions, the most likely to be on the sheet.

**Cause:** Browsers do not break a line after "/", so "Regierungschefinnen/Regierungschefs" is one 35-letter
word. The options are a CSS grid, and a grid column grows to its widest unbreakable content (min-content), so one
long word widened all four buttons past the card: `.options` was 276 px wide, its buttons 331 px.

**Fix:** `<wbr>` after every "/" (`SoftBreaks` in `app/src/components/Text.tsx`) in question, option and feedback
text, plus `grid-template-columns: minmax(0, 1fr)` and `overflow-wrap: anywhere` as a last resort. After the fix the
same sweep found 0 of 310 at 375 px and at 340 px, also with the feedback and the "why" block open.

**Consequences:** Check new screens at 340-375 px with the real catalog text, not with short sample strings; the
catalog has dozens of "-innen/-en" pairs. Headless Chrome on the command line cannot go below about 500 px
(`--window-size=390` gave `innerWidth` 512), so use Playwright's viewport for phone checks.
