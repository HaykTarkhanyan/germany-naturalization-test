# Einbürgerungstest (German naturalization test) - Munich / Bayern

Everything needed to prepare for the "Leben in Deutschland" / Einbürgerungstest as a Munich resident:
the official question catalog, all 310 Bayern questions with verified answers, the practical
steps in Munich, and a survey of existing tools. Facts checked on 2026-10-02.

## What is in this repo

| Path | What it is |
|---|---|
| [`QUESTIONS_AND_ANSWERS_BAYERN.md`](QUESTIONS_AND_ANSWERS_BAYERN.md) | All 310 questions (300 general + 10 Bayern) with the correct answer marked, picture questions included. Start here. |
| [`data/questions_bayern.json`](data/questions_bayern.json) / [`.csv`](data/questions_bayern.csv) | Same, machine-readable (for Anki, a quiz app, an LLM, ...) |
| `data/topics.json` | The 310 questions grouped into 24 study topics (in the 3 BAMF course modules + Bayern), ids in study order with related questions next to each other |
| `data/images/` | The 13 picture questions (coats of arms, flags, photos) as served by BAMF |
| `data/raw/` | Raw scrape of the BAMF Online-Testcenter - the record the dataset is built from |
| `official/gesamtfragenkatalog-lebenindeutschland_2025-05-26.pdf` | Official BAMF catalog, all 460 questions incl. all 16 states, "Stand 07.05.2025". **No answers in it.** |
| `official/musterbogen_einbuergerungstest.pdf` | Official sample answer sheet (a real Bayern sheet), shows what the paper test looks like |
| `official/musterbogen_einbuergerungstest_2008_berlin.pdf` | The previous official sample sheet (Berlin, 2008; on bamf.de until ~2021, recovered via the Wayback Machine) |
| `official/einbuergerungstest-pruefungsordnung.pdf` | Official exam regulations (BAMF) |
| `official/Pruefstellen-BY.xlsx` | Official list of all 116 test centers in Bayern |
| [`PATTERNS.md`](PATTERNS.md) | Are there answer shortcuts? Tested 41 rules + 1,456 conditional rules: what works, what is a myth, and a rule list that halves what you must memorize |
| `reports/patterns_report.html` | Interactive report for the pattern analysis, incl. your ordered study list (open in a browser) |
| `results/patterns.json` | Raw results of the pattern analysis (the report is built from it) |
| [`RESOURCES.md`](RESOURCES.md) | GitHub repos, datasets, apps, bots, AI tools - what exists and what is worth using |
| `scripts/` | Dataset build (scraper + `build_dataset.py`) and pattern analysis (`mine_patterns.py`, `build_pattern_report.py`) |

## Where the answers come from (and why you can trust them)

The official PDF has the questions but does **not** say which answer is right. The answers come from
BAMF's own practice site, the [Online-Testcenter](https://oet.bamf.de/ords/oetut/f?p=514:1:0)
(Bundesland = Bayern), scraped on 2026-10-02. The question text comes from the PDF, because the
Online-Testcenter shows the question as an image (and for 12 questions shows no question at all).

Checks run by `scripts/build_dataset.py` and by hand:

- All 310 questions present, 4 options each, exactly one marked correct.
- PDF options and Online-Testcenter options match one-to-one for all 310 (only cosmetic differences
  like "der Bundespräsident / die Bundespräsidentin" vs "die Bundespräsidentin/der Bundespräsident").
- Cross-checked against two independent GitHub datasets:
  - [youssefeghaly/einbuergerungstest](https://github.com/youssefeghaly/einbuergerungstest): **310/310 identical answers**.
  - [vlad-ds/anki-german-citizen-test](https://github.com/vlad-ds/anki-german-citizen-test) (popular Anki deck): 300/310. All 10 differences checked by hand; the deck is outdated or wrong on every one (Scholz instead of Merz, old Bundestag factions, wrong coat-of-arms pictures, and it says you vote in Bavarian local elections at 16 - it is 18). **Do not study from that deck.**

## The test in one paragraph

33 multiple-choice questions (30 from the 300 general ones + 3 of the 10 Bayern ones), 4 options
each, exactly one correct, 60 minutes, paper and pencil. **17 correct = pass.** Fee 25 EUR, paid at
the test center. Every candidate gets a different question sheet. Only the sheet and pens are allowed
on the desk; phones and any device that can store or transmit information are forbidden within reach,
even if nothing is stored on them. Bring a valid (not expired) passport or ID card with photo. The
result is evaluated centrally by BAMF and the certificate is sent **by post**: "erfolgreich
teilgenommen" = passed, "teilgenommen" = took part, not passed. No retake limit; each attempt costs
25 EUR again. If you did an integration course, a "Leben in Deutschland" result of 17/33 or more
also counts (it is the same question pool).

**Plan for the certificate delay.** On 2026-09-28 BAMF wrote: "Aktuell wertet das Bundesamt Tests
bis Prüfungsdatum 09.07.2026 aus" - i.e. the certificate arrives roughly **12 weeks** after the test.
Book the test well before you want to submit the naturalization application.

## Munich, step by step

1. **Check eligibility** (current law, StAG as changed 27.06.2024 and 30.10.2025):
   - 5 years of lawful, habitual residence in Germany. The 3-year "Turbo-Einbürgerung" was abolished,
     in force since 30.10.2025.
   - Unlimited residence right (or a qualifying permit), secured livelihood (generally without Bürgergeld).
   - German at **B1** (certificate, or a German school or university degree).
   - Einbürgerungstest passed. Not needed if you have a Mittelschulabschluss (Bavarian lower-secondary
     certificate) or higher from a German general school, a completed apprenticeship in a Lehrberuf, or a
     degree from a German university in law / social sciences / political science; medical exemptions exist too.
   - Commitment to the free democratic order, incl. Germany's historic responsibility. Antisemitic or
     racist convictions are an absolute bar.
   - Multiple citizenship is allowed (your other country may still take its nationality away - check that).
   - Munich's own [Quick-Check](https://service.muenchen.de/intelliform/forms/01/02/02/einbuergerung-quick-check/index) tells you quickly if you qualify.
2. **Book the test** at a test center (all registrations in Munich are **in person**, not online):
   - **Münchner Volkshochschule (MVHS)** - [test dates](https://www.mvhs.de/kurse/460-CAT-KAT7869). As of 2026-10-02 the next dates were 25.11.2026, 11.12.2026 and 22.01.2027, 25 EUR, up to 200 people per date, exam at Orleansstr. 34 (window 09:00-14:00). Register in person with your passport/ID at Einsteinstr. 28 or MVHS im HP8 (Hans-Preißinger-Str. 4), Mon-Sat 8:30-19:00, or Orleansstr. 34, Mon-Fri 9:00-13:00. Dates can sell out before the registration deadline. Cancelling/rebooking costs 10 EUR until a cutoff, nothing possible after (for 25.11.2026: cutoff 10.10.2026). Your exact time comes ~10 days before (the page says e-mail in one place and post in another).
   - **Bayerisches Rotes Kreuz (BRK)** - [page](https://www.brk-muenchen.de/start/angebote/migration-integration/einbuergerungstests.html). Goethestr. 53, room 108. Registration without appointment Wed 8-12 and 14-18, Thu 8-15, Fri 8-13. October was booked out; next dates 18.11., 21.11. and 25.11.2026 (Wed 14:00/15:30/17:00, Sat 10:00-16:00 in five slots). 25 EUR, **card only**. Free rebooking up to 25 days before; cancelling later means paying again (waived with a doctor's note). Paper test, German only, pen provided.
   - Other official test centers in Munich city: Inlingua (Sendlinger-Tor-Platz 6), Anderwerk (Hamburger Str. 32), DAA (Marsstr. 42), MAS Sprachschule (Goethestr. 12), Bildungsinstitut Kavalchuk (Leopoldstr. 244). In the Landkreis: VHS Nord (Garching), VHS SüdOst (Ottobrunn), Taufkirchen, Unterhaching, Oberschleißheim. Full list with phones and e-mails: `official/Pruefstellen-BY.xlsx`.
   - The regulations oblige the test center to give you a slot **within 12 weeks** of registering.
3. **Study:** `QUESTIONS_AND_ANSWERS_BAYERN.md`. The real questions are word-for-word from this pool,
   so memorizing the 310 works. Watch the Bayern traps: local elections from **18** (not 16 as in many
   states), Landtag elected for **5** years, Bayern has no Außenminister, the flag is **weiß-blau**,
   the head of government is the Ministerpräsident(in).
4. **Apply** to the KVR Einbürgerungsbehörde (Ruppertstraße 19, entrance 19A, 80337 München, phone 115):
   - The city asks for the [online application](https://service.muenchen.de/intelliform/forms/01/02/02/einbuergerung/index), complete, with all documents uploaded. You need a BundID or BayernID; username and password are enough, no online ID card required. You pay before submitting. A paper application by post is still accepted (invoice at the end).
   - Fee: **255 EUR** per adult, 51 EUR per minor child naturalized together with a parent.
   - Documents: passport, residence permit, income proof, B1 certificate, test certificate (or the qualifying diploma), birth certificate if born in Germany.
   - Processing time stated by the city: **"18 Monate und länger"**. Part of the reason: security-agency checks currently take 4-6 months on their own. An incomplete file only makes it slower. Expiring documents, travel plans or buying property are not reasons to speed it up.

## Rebuild the dataset

```
python scripts/build_dataset.py      # ~4-12 s, stdlib only, needs pdftotext (poppler) on PATH
```

Pattern analysis (needs `uv sync` once; plotly is pinned in `pyproject.toml`):

```
python scripts/check_sheet_order.py             # ~30 s -> results/sheet_order_check.json (option order on official sample sheets)
uv run python scripts/mine_patterns.py          # ~6 s  -> results/patterns.json
uv run python scripts/build_pattern_report.py   # ~5 s  -> reports/patterns_report.html (needs both JSONs)
```

To re-scrape the answers (e.g. after BAMF publishes a new catalog), follow the header of
`scripts/oet_scrape.js` (~8 min via the Playwright MCP server). If the PDF changes, also update the
`PDF` path in the build script.

## Sources

- BAMF, catalog download: https://www.bamf.de/SharedDocs/Anlagen/DE/Integration/Einbuergerung/gesamtfragenkatalog-lebenindeutschland.html
- BAMF, Einbürgerung page (test facts, backlog, test-center lists): https://www.bamf.de/DE/Themen/Integration/ZugewanderteTeilnehmende/Einbuergerung/einbuergerung-node.html
- BAMF Online-Testcenter: https://oet.bamf.de/ords/oetut/f?p=514:1:0
- Landeshauptstadt München, Einbürgerung: https://stadt.muenchen.de/service/info/einburgerungsbehorde/1080548/
- MVHS Einbürgerungstest dates: https://www.mvhs.de/kurse/460-CAT-KAT7869
- BRK München Einbürgerungstests: https://www.brk-muenchen.de/start/angebote/migration-integration/einbuergerungstests.html
- Abolition of the 3-year track (Bundestag 08.10.2025, in force 30.10.2025): https://www.anwalt.org/turbo-einbuergerung-abgeschafft-nach-nur-einem-jahr-ist-schluss/ and https://www.bmi.bund.de/SharedDocs/gesetzgebungsverfahren/DE/VII5/gesetz-6-aenderung-des-staatsangehoerigkeitsrechts.html
- Verordnung zum Einbürgerungstest (EinbTestV): https://www.gesetze-im-internet.de/einbtestv/
