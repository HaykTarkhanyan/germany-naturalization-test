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
- **Pattern report: TOC + collapsible sections** - `reports/patterns_report.html` was built before the global HTML rule (sections collapsible, table of contents on top); rebuild `scripts/build_pattern_report.py` to follow it.
- **Video renderer into the repo** - `demo_render.py`, `tts_check.py` and the listening-page builder still live in the session scratchpad; move them to `videos/pipeline/` (logging, pinned deps) so the videos in `videos/mp4/` can be rebuilt from the repo (DECISIONS #20).
- **Re-render videos 01-06 frames** - they were rendered before cards closer than 2 s were grouped into one grid; a re-render from the cached audio costs no API calls (needs videos/build/ from this machine).
- **Pronunciation hints for German terms in Russian narration** (`videos/pronunciation.json`) - only if listening shows mispronounced terms.
- **Words page: "known" tick per word** - track which words are learned, like the question progress.
- **Subtitles: merge very short chunks** - the renderer splits at every `.`, `!`, `?`, `:` (and `;` since the recap fix), so cue-like bits ("To memorize:", "1945.") show alone for under a second. Packing neighbours up to ~95 characters would change most videos; re-render from cached audio, no API cost.

