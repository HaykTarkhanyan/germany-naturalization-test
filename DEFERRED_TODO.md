# Deferred TODO

Parked ideas, not started.

- **Practice quiz** - a small offline HTML page that draws 30 general + 3 Bayern questions from `data/questions_bayern.json` like the real test, with spaced repetition on wrong answers.
- **Anki deck** - build an `.apkg` from the CSV incl. the 13 images (e.g. with `genanki`).
- **English translations / explanations** - for questions where the German is hard. Could borrow from abdullahbutt or leben-in-deutschland (both MIT) instead of generating new ones.
- **Printable PDF** of `QUESTIONS_AND_ANSWERS_BAYERN.md` (pandoc or Edge headless) for phone/print.
- **Re-check for a new catalog** - BAMF catalog page shows "DATUM 26.05.2025" today. If it changes, re-download the PDF, re-run `scripts/oet_scrape.js`, rebuild.
- **Other states** - only if moving away from Bayern (see DECISIONS.md #2).
- **Pattern analysis follow-ups** - (a) model guessing after crossing out options (guess probability 1/3 or 1/2 instead of 1/4; needs a Poisson-binomial instead of the 3-category exact model); (b) when BAMF publishes a new catalog, score the current rule list on the new/changed questions only - a true out-of-sample test.
- **Commit the cross-check probe** as `scripts/non_essential/` tooling if catalog updates make it worth re-running.
- **Pattern report: TOC + collapsible sections** - `reports/patterns_report.html` was built before the global HTML rule (sections collapsible, table of contents on top); rebuild `scripts/non_essential/build_pattern_report.py` to follow it.
- **Pronunciation hints for German terms in Russian narration** (`videos/pronunciation.json`) - only if listening shows mispronounced terms.
- **Words page: "known" tick per word** - track which words are learned, like the question progress.
- **Offline / install on the phone (PWA)** - a web app manifest and a service worker so the site opens without network (U-Bahn). Cut from the 2026-10-26 UX round: a cached old version after a deploy is the classic PWA bug, and the videos (114 MB) must not be pre-cached.
- **Flag a question** - a star on a question to collect hard ones by hand. Cut on 2026-10-26: "My mistakes" (DECISIONS #24) covers most of it automatically.
- **Russian question translations in the app** - `data/translations_ru.json` (all 310 questions and answers, DECISIONS #25) is used only by the Russian study files so far. The app's translation line under each question could follow the explanation language (Russian instead of English) when Hayk wants it.
- **Committed UI tests** - every UI check so far was a one-off Playwright run; a small `@playwright/test` suite (practice, exam keys, mistakes, search, phone width) in `npm test` and the deploy would have caught the exam focus bug of 2026-10-26. Adding a test framework is Hayk's choice (asked as Q6 in the 2026-10-26 review).
- **Skip the deploy for doc-only pushes** - every push to main rebuilds and uploads the 114 MB site (77 s). A `paths` filter on `.github/workflows/pages.yml` (app/, data/, videos/scripts/, videos/mp4/, the workflow) would skip README/log commits; a wrong filter means a stale site, so test it.
- **Split the app bundle** - Vite warns that the main chunk is over 500 kB (1,034 kB, 270 kB gzipped, measured 2026-10-26: all data is bundled). Fine on 4G; lazy-load the vocabulary and video texts if the first load ever feels slow.
- **Back up the voice cache** - `videos/build/render/*/sN.wav` (~250 MB, this machine only) is what makes re-renders free; losing it means re-voicing all 226 scenes for ~$1.30 (`render.py all --tts`). Copy it somewhere safe if the laptop is replaced.

