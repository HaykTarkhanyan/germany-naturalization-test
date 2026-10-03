# Decisions

Newest first.

## 10. "Known" = the last two answers to a question were right; the pass chance counts only known questions as sure

- **Date / status:** 2026-10-03, active
- **Why:** One right answer is weak evidence: in practice the right answer was often just shown, and a blind guess is right 25% of the time. Two right answers in a row is the simplest rule that filters both, and it is easy to explain on screen. The pass chance then uses the exact exam model from `mine_patterns.py` with two kinds of question (known = always right, everything else = guessed at 25%), ported to `app/src/lib/exam.ts` and unit-tested against independent Python values (0.0009509599956171568 for nothing known, 0.9360898856228623 for 150 + 5 known; matches to 10 decimals). Conservative on purpose: "learning" questions you would often get right count as guesses.
- **Alternatives rejected:** last answer only (counts lucky guesses and just-seen answers as known); a per-question probability from the whole history (needs a Poisson-binomial over draws without replacement, and is harder to explain); FSRS retrievability (spaced repetition was not chosen for this app).
- **What would change this:** Mock exam scores running clearly above the predicted expected score (then the rule is too strict).

## 9. Study app: nemeceren's frontend stack, browser-only progress, three modes, GitHub Pages

- **Date / status:** 2026-10-03, active (stack, storage, modes and hosting chosen by Hayk)
- **Why:** Hayk asked for an app and pointed at `misc/nemeceren` as the stack reference, so it is the same toolchain at the same pinned versions that already run on Node 20.20.0 there: Vite 8.3.1, React 19.3.0, TypeScript 6.0.3, zod 4.6.5, Vitest 4.1.11, plain CSS with variables, the 20-line hash router, and the same Pages workflow. Hayk chose: progress in the browser's localStorage with export/import (no backend), the modes topic practice + mock exam + progress/pass chance (no spaced repetition), hosting on GitHub Pages. The app imports `data/` directly (no copy) and validates it with zod at startup; invalid stored progress is shown with a download-then-reset screen, never silently replaced.
- **Alternatives rejected (offered to Hayk):** reusing nemeceren's Neon backend for PC/phone sync (couples the two projects); a new Neon project (most work for a few weeks of use); local-only hosting (no phone access). Spaced repetition (FSRS via ts-fsrs) was offered as a mode and not chosen.
- **What would change this:** Studying regularly on both phone and PC (then sync via nemeceren's backend), or wanting daily review scheduling (then ts-fsrs like nemeceren).

## 8. Study topics: hand-curated grouping in data/topics.json, separate from the question data

- **Date / status:** 2026-10-03, active
- **Why:** For studying topic by topic. 24 topics of 6-20 questions, nested in the three modules of the official BAMF Orientierungskurs curriculum (Politik in der Demokratie / Geschichte und Verantwortung / Mensch und Gesellschaft) plus Bayern. Assigned by reading all 310 questions; within a topic, related questions are adjacent (e.g. all Bundespräsident questions together) so near-identical answers get learned side by side. Kept as its own file (ids only) so `build_dataset.py` and the topic choice can change independently. Validated: 310 ids, 310 unique, none missing.
- **Alternatives rejected:** The leben-in-deutschland project's `category` field (lopsided: "History & Geography" 169 of 460, "Press Freedom" 1; different numbering); keyword-based automatic grouping (not tried; would misfile questions like 216 "Bundesadler im Plenarsaal"); catalog order alone (roughly topical but scattered, e.g. Wahlhelfer at 105/106 and 282).
- **What would change this:** A new BAMF catalog (new ids must be placed), or study sessions showing a topic is too big to learn in one go (split it).

## 7. Treat the option order on the real exam as unverified; report both scenarios

- **Date / status:** 2026-10-02, active
- **Why:** Both official BAMF sample sheets (2008 Berlin, 2021 Bayern) print options in catalog order (56/56 checkable questions), but EinbTestV § 1 (2) says the 100 real sheets are not published and no rule fixes the option order. So every strategy number that depends on positions (always B, the B/D/A/C fallback) is reported next to a shuffled-options scenario: 95%-pass memorization need is 64 if order is kept, 100 if shuffled, 148 without rules.
- **Alternatives rejected:** Assuming catalog order (overclaims from sample sheets; this was the first version and the user questioned it); assuming shuffling (contradicted by all available sheets).
- **What would change this:** A photo or first-hand report of a real exam sheet with options in a different order (-> drop the position fallback), or more real sheets in catalog order (-> keep it with more confidence).

## 6. Pattern analysis: in-sample numbers are the headline, cross-validation is the honesty check

- **Date / status:** 2026-10-02, active
- **Why:** The exam is drawn from exactly these 310 questions, so a rule only has to work on them; in-sample precision is what you get on test day. But with 41 rules + 1,456 conditional rules + every word tested, many good-looking numbers are luck, so every learned or mined component is also re-fit on 4/5 and scored on the held-out 1/5 (seed 509), and rule verdicts use Bonferroni. Mined rules (key numbers, word lists) come from the answers themselves and are excluded from the cross-validated rule list. The ranking metric for usefulness is net gain = hits - misses (the misses are exceptions you would have to remember).
- **Measured:** rule list 40% in-sample vs 30% held-out; naive Bayes words+features 56% train vs 39% held-out; conditional rules 34% held-out.
- **Alternatives rejected:** CV-only reporting (understates what the rules give on this closed pool); in-sample-only (would sell overfit rules like "question has 'bayern' -> odd_length 4/5" as real).
- **What would change this:** A new BAMF catalog - then held-out numbers become the relevant ones for the changed questions.

## 5. Exam pass probability computed exactly, not by Monte Carlo

- **Date / status:** 2026-10-02, active
- **Why:** With per-question outcomes in {right, wrong, guess at 25%}, P(pass) is an exact sum over multivariate hypergeometric draws (30/300 general, 3/10 Bayern) times a binomial tail - deterministic, ~ms per evaluation, which makes the 311-point memorization curves cheap. Verified against a 20,000-draw simulation: 0.0071 vs 0.0069 (always B), 0.9361 vs 0.9354 (half memorized).
- **Alternatives rejected:** Monte Carlo (noisy, slower, and 311 curve points x many draws is heavy on this laptop).
- **What would change this:** Strategies with per-question guess probabilities other than 25% (e.g. after crossing out options) - those need a Poisson-binomial or simulation.

## 4. Analysis environment: uv project with plotly==7.1.0 for the report

- **Date / status:** 2026-10-02, active
- **Why:** Plotly is the stated default for interactive reports; the report inlines plotly.js so it works offline as one file. Only dependency; everything else is stdlib. Pinned to the version installed and verified (7.1.0, bundles plotly.js 4; the bar/line charts used needed no v7 changes per the plotly docs).
- **Alternatives rejected:** matplotlib static report (no hover/zoom); adding pandas/scipy (not needed: binomial tails and Wilson CIs are a few lines).
- **What would change this:** Needing statistical models beyond naive Bayes (then scikit-learn).

## 3. Build script uses only the stdlib plus `pdftotext`

- **Date / status:** 2026-10-02, active
- **Why:** The build is a one-shot text transformation (parse PDF text, merge with scraped JSON, write JSON/CSV/MD). `pdftotext -layout` (poppler, already installed) gives clean per-line output with the option checkboxes as `U+F0A3` / `U+25A1`, so no PDF library is needed. No dependencies means nothing to pin and nothing to break.
- **Alternatives rejected:** `pdfplumber`/`pypdf` (extra dependency for no gain); `pdftotext` without `-layout` (moves the tail of wrapped question stems to other lines, e.g. Q281 and Q288 came out truncated).
- **What would change this:** BAMF changing the PDF layout so that `-layout` output stops being line-structured.

## 2. Scope: Bayern only (310 questions), not all 16 states

- **Date / status:** 2026-10-02, active
- **Why:** The user lives in Munich, so only the 300 general + 10 Bayern questions can appear in their test. The Online-Testcenter serves one state per session; scraping all 16 would be ~16x the requests for questions that are irrelevant here.
- **Alternatives rejected:** All 460 questions with answers (the PDF in `official/` has all 160 state questions, just without answers). youssefeghaly/einbuergerungstest already has all 460 if ever needed.
- **What would change this:** Moving to another state, or wanting to publish a full dataset.

## 1. Answers come from the BAMF Online-Testcenter, question text from the BAMF PDF, displayed options from the PDF

- **Date / status:** 2026-10-02, active
- **Why:** The official PDF (Stand 07.05.2025) has no answer key. The only official source of correct answers is the Online-Testcenter (oet.bamf.de), which marks the correct option in the HTML (`id="FARBE"`) but renders the question stem as an image (and shows no stem at all for 12 questions). So: stem text from the PDF, correct index from the OET. Option order is identical in both (verified for all 310 by word-level similarity), so the index transfers to the PDF wording, which is newer (female-first gender pairs, "Bild 1" instead of "1") and matches the question text. The OET wording is kept as `options_oet`.
- **Alternatives rejected:** Copying a GitHub dataset (third-party, may be stale - the popular vlad-ds Anki deck was wrong on 10/310); OCR of the OET stem images (lossy, and 12 stems are missing anyway); clicking each answer on the OET (unnecessary, the marker is in the DOM).
- **Verification:** 310/310 agreement with youssefeghaly/einbuergerungstest; all 10 disagreements with vlad-ds resolved in our favor by hand (see `_learnings/2026-10-02-1335_crosscheck-github-datasets.md`).
- **What would change this:** BAMF publishing an official answer key, or the OET removing the `FARBE` marker.
