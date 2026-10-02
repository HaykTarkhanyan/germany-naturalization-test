# Resources - repos, datasets, apps, AI tools

Surveyed 2026-10-02. Stars and "last push" dates are from that day. "Checked" means I downloaded the
data and compared it against `data/questions_bayern.json`; everything else is from the repo
description only.

## Bottom line

- **For studying:** use `QUESTIONS_AND_ANSWERS_BAYERN.md` in this repo, or the official
  [BAMF Online-Testcenter](https://oet.bamf.de/ords/oetut/f?p=514:1:0) (pick Bayern). The
  Online-Testcenter has one flaw: for 12 questions (14, 59, 66, 96, 111, 118, 149, 182, 184, 206,
  234, 288) it shows the answers but no question text.
- **For building something:** youssefeghaly's or the leben-in-deutschland project's JSON are
  solid and cover all 16 states. Ours covers Bayern only but is freshly re-derived from both official
  BAMF sources.
- **Avoid** the vlad-ds Anki deck (outdated, see below).
- **AI / agentic:** almost nothing serious exists. No MCP server, no Hugging Face dataset, no
  published LLM benchmark on this test. A few small hobby apps with an "AI tutor".

## Machine-readable datasets

| Repo | Stars | Last push | What | Verdict |
|---|---|---|---|---|
| [youssefeghaly/einbuergerungstest](https://github.com/youssefeghaly/einbuergerungstest) | 0 | 2026-09-29 | `data/questions.json`, all 460, catalog 07.05.2025, answer key from the leben-in-deutschland project. Python tools to extract the PDF. Site: einburgerungstestdeutschland.vercel.app | **Checked: 310/310 answers identical to ours.** Best data source found. |
| [leben-in-deutschland/leben-in-deutschland-app](https://github.com/leben-in-deutschland/leben-in-deutschland-app) + [-scrapper](https://github.com/leben-in-deutschland/leben-in-deutschland-scrapper) | 10 / 3 | 2026-10-01 | Open-source app ([lebenindeutschland.org](https://www.lebenindeutschland.org/)), MIT. `question.json` with AI translations into 7 languages, `prüfstellen.json` (all test centers, all states) | Most active project. Its test-center list is stale for Munich (one center not on the official list, one missing, one old address) - use `official/Pruefstellen-BY.xlsx` instead. |
| [abdullahbutt/leben-in-deutschland-test](https://github.com/abdullahbutt/leben-in-deutschland-test) | 25 | 2026-09-29 | All 460 with translations (EN, UR, AR, TR, RU) and explanations, MIT. Site: leben.wordfeather.com | Most starred. Not checked. |
| [JadRizk/einbuergerungstest-trainer](https://github.com/JadRizk/einbuergerungstest-trainer) | 0 | 2026-09-18 | All 460 with English explanations of civic terms, offline PWA | Not checked. |
| [Chase22/german-citizenship-questions](https://github.com/Chase22/german-citizenship-questions) | 0 | 2025-08-05 | Kotlin scraper + JSON schema, GPL-3.0 | Not checked. |
| [webmansa/german-citizenship-test-data](https://github.com/webmansa/german-citizenship-test-data) | 1 | 2025-11-09 | JSON catalog | Not checked. |

## Anki decks

| Repo | Stars | Last push | Verdict |
|---|---|---|---|
| [vlad-ds/anki-german-citizen-test](https://github.com/vlad-ds/anki-german-citizen-test) | 21 | 2025-07-20 | **Checked: 10 of 310 Bayern answers are wrong or outdated.** Old chancellor (Scholz), old Bundestag factions, wrong answers for the 5%-hurdle and occupation-zones questions, all three general picture questions answered "Bild 3" (wrong), and Bayern local-election age 16 (correct: 18). Avoid. |
| [ignamv/einbuergerungstest](https://github.com/ignamv/einbuergerungstest) | 13 | 2024-08-15 | Python scraper that builds Anki decks for all states. Last push predates the 2025 catalog and the 2025 election, so expect the same staleness. Not checked. |

If you want Anki: import `data/questions_bayern.csv` (columns: question, options a-d, answer letter,
answer text, image path).

## Practice apps and sites (open source)

- [flexsurfer/einburgerungstest](https://github.com/flexsurfer/einburgerungstest) - "05.2025 Einbürgerungstest", web + mobile ([ebtest.org](https://www.ebtest.org/)), MIT, 4 stars.
- [kailashbuki/einbuergerungstest](https://github.com/kailashbuki/einbuergerungstest) - mobile-first, offline-first study app.
- [bhavin-ch/german-citizenship-test](https://github.com/bhavin-ch/german-citizenship-test) - browser-only practice app.
- [thelivinsine/eib-quiz](https://github.com/thelivinsine/eib-quiz) - bilingual DE/EN quiz (Berlin).

## AI / agentic

Nothing mature. What exists:

- [rksekar5/einburgerungstest-trainer](https://github.com/rksekar5/einburgerungstest-trainer) - Next.js, Leitner spaced repetition, "fact-bounded AI tutor via Vercel AI Gateway". 0 stars.
- [AntonSk98/Einbuergerung-Bot](https://github.com/AntonSk98/Einbuergerung-Bot) - "smart companion... adaptive learning and official mock exams".
- [mykytakuzminov/dld-quiz-bot](https://github.com/mykytakuzminov/dld-quiz-bot) - Telegram quiz bot (learn / exam / stats). Hosted demo is offline; runs locally via Docker.
- [ishara-madu/German-Citizenship-Test-Android-App](https://github.com/ishara-madu/German-Citizenship-Test-Android-App) - "AI-powered" Kotlin/Compose app.
- The leben-in-deutschland project uses an LLM to translate questions into 7 languages.

Searched and found nothing: MCP servers for this test, Hugging Face datasets or Spaces (the closest
is a Danish citizenship-test dataset, `sorenmulli/citizenship-test-da`), and published LLM benchmarks on the Einbürgerungstest.

## Appointment checkers

All for Hamburg or Berlin, where test centers have online booking:
[tobiasraabe/hamburg-einbuergerungstest-terminfinder](https://github.com/tobiasraabe/hamburg-einbuergerungstest-terminfinder) (Rust),
[hossys/termin-checker](https://github.com/hossys/termin-checker) (VHS Hamburg),
[ghazalak/Berlin-Einbuergerungstest-Termin](https://github.com/ghazalak/Berlin-Einbuergerungstest-Termin),
[Hippedihop/einbuergerungstestanmeldung-terminchecker](https://github.com/Hippedihop/einbuergerungstestanmeldung-terminchecker).
None for Munich, and a bot would not help here: MVHS and BRK only take registrations in person.

## Official sources

- [BAMF catalog page](https://www.bamf.de/SharedDocs/Anlagen/DE/Integration/Einbuergerung/gesamtfragenkatalog-lebenindeutschland.html) - check the "DATUM" there to see whether a newer catalog than 26.05.2025 is out.
- [BAMF Einbürgerung page](https://www.bamf.de/DE/Themen/Integration/ZugewanderteTeilnehmende/Einbuergerung/einbuergerung-node.html) - test facts, current certificate backlog, test-center lists per state.
- [BAMF Online-Testcenter](https://oet.bamf.de/ords/oetut/f?p=514:1:0) - official practice with answers.
- [München: Einbürgerung](https://stadt.muenchen.de/service/info/einburgerungsbehorde/1080548/) - requirements, fees, online application, Quick-Check.
