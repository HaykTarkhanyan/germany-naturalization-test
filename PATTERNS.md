# Answer patterns in the Einbürgerungstest (Bayern pool, 310 questions)

Analysis run 2026-10-02 on `data/questions_bayern.json`. Raw results: `results/patterns.json`.
Interactive report with all charts and the full study list: `reports/patterns_report.html`.
Rebuild: `python scripts/check_sheet_order.py` (~30 s), `uv run python scripts/mine_patterns.py` (~6 s), then
`uv run python scripts/build_pattern_report.py` (~5 s).

## Verdict

**No trick passes the test on its own, but the good ones cut what you have to memorize by more than half.**

| Strategy (nothing memorized) | Expected score | P(pass, 17/33) |
|---|---|---|
| Blind guessing | 8.2 / 33 | 0.1% |
| Always answer B | 10.2 / 33 | 0.7% |
| Always the longest answer | 9.3 / 33 | 0.2% |
| Rule list below, applied to these 310 questions | 13.4 / 33 | 12.2% |
| Same, if the exam shuffles the options (fallback = guess) | 11.5 / 33 | 3.3% |
| Best pattern model, scored on questions it did not see | 12.7 / 33 | 7.6% |

Answers to memorize for a given pass chance ("avg. 17/33" = your expected score reaches the pass mark, a minimal
pass on average; 50% = coin flip):

| Memorize, then for the rest... | avg. 17/33 | 50% | 60% | 70% | 80% | 90% | 95% | 99% |
|---|---|---|---|---|---|---|---|---|
| guess | 97 | 91 | 100 | 109 | 120 | 136 | 148 | 171 |
| use the rule list, **if the exam shuffles the options** (fallback = guess) | 49 | **43** | 52 | 61 | **72** | 88 | **100** | 123 |
| answer B (only if the exam keeps catalog order) | 56 | 52 | 58 | 65 | 73 | 85 | 94 | 110 |
| use the rule list, catalog order kept | 26 | **22** | 28 | 35 | **43** | 55 | **64** | 80 |

- The shuffled-options rule list is exactly **48 answers** cheaper than plain guessing at every level: the content
  rules answer 48 questions correctly for free, and the 21 they get wrong you memorize anyway.
- Safety gets expensive at the top: 50% -> 90% costs 6-16 extra answers per 10 points, 95% -> 99% alone costs
  16-23.
- For context: the national pass rate is reported at about 96-98%.

Whether the printed exam keeps the catalog's option order is **not proven** - see "Option order on the real exam"
below. The content rules (1-6) work either way; only the B/D/A/C fallback depends on it.

Memorizing order: the 10 Bayern questions first (each is 3x as likely to be on your sheet as a general one: 3/10 vs
30/300), then the questions the strategy gets wrong. The report has that ordered list ("Your study list").

## The rule list (use in order, first match decides)

| # | Rule | Right |
|---|---|---|
| 1 | Numeric question: pick the one option that is a **key number: 4, 5, 18, 1933, 1949, 1961** | 10/10 |
| 2 | "Which state belonged to the DDR?": the one of Brandenburg, Sachsen, Sachsen-Anhalt, Thüringen, Mecklenburg-Vorpommern | 5/5 |
| 3 | "Which country is a neighbour?": the one of Dänemark, Polen, Tschechien, Österreich, Schweiz, Frankreich, Luxemburg, Belgien, Niederlande | 5/5 |
| 4 | The only option with an official-channel word (**Einspruch, Widerspruch, Gericht, Behörde, Beratung**, Klage, Anwalt) | 7/10 |
| 5 | The only option with a democratic-values word (**Freiheit, gleich, Würde, Demokratie, Grundgesetz, Frieden**, ...) | 13/24 |
| 6 | Numeric question: the **second-highest** number | 8/15 left after rule 1 (12/25 overall) |
| 7 | Otherwise: cross out the options below, then take the first remaining in the order **B, D, A, C** (only meaningful if the sheet keeps catalog order; otherwise guess among the rest) | 76/241 |

**Cross out** (almost never right):
- Options mentioning **Polizei** (0/6), "do nothing / ignore it" options (nichts, ignorieren, egal, wegwerfen: 0/8)
- Options with the words **Bundesregierung** (0/8), **gehen** (0/7), **dürfen** (0/9). Never-right words as a
  group held up on held-out questions too: the 11 such words mined on training splits were 0 of 23 on the
  held-out options
- Options that themselves contain nicht/kein (3/23)
- In numeric questions, the **lowest** number (1/25) and, less strongly, the highest (5/25)

Bonus memory aid: an option saying **18** was right every time it appeared (3/3: voting age, age of majority,
Bavarian local elections - Bayern did not lower that to 16).

These rules get 124 of 310 right (40%). Fitted on 4/5 of the questions and tested on the other 1/5 they get 30%,
so they are a memory aid for this exact pool, not a law of how BAMF writes questions. Since your exam is drawn from
exactly this pool, the 40% is what you get if you apply them.

## What does not work

| Popular trick | Right when it applies | |
|---|---|---|
| Longest answer | 71/253 = 28% | barely above guessing (25%) |
| Longest answer by words | 40/137 = 29% | same |
| Shortest answer | 60/239 = 25% | same as guessing |
| "Centre" option (shares most words with the others) | 13/41 = 32% | weak |
| Always B | 94/310 = 30% | most common position, but p = 0.019 uncorrected, not significant after correction |
| Numbers: pick the lowest | **1/25 = 4%** | the opposite is true |
| Absolute words (nur, immer, alle) are wrong | 16/74 options right = 22% | only slightly worse than a random option |
| Violence / monarchy / money words are wrong | 20-29% of such options right | not the giveaway you would expect |
| Question has nicht/kein -> longest answer | 5/26 = 19% | no |
| "If the question contains word X, then Y" | 1,456 combinations tested | none survives multiple-testing correction; mined rules were right 34% (46/134) on held-out questions |

## Option order on the real exam

Checked 2026-10-02 (`scripts/check_sheet_order.py` -> `results/sheet_order_check.json`):

| Source | What it says |
|---|---|
| Official BAMF sample sheet, Bayern, Dec 2021 (current on bamf.de) | 30/30 checkable questions in catalog order |
| Official BAMF sample sheet, Berlin, 2008 (bamf.de until ~2021, via Wayback Machine and innen.hessen.de) | 26/26 checkable questions in catalog order |
| EinbTestV § 1 (2) | "Die aus dem Fragenkatalog in Anlage 1 erstellten 100 Fragebögen enthalten 33 Fragen ... Die Fragebögen werden nicht veröffentlicht." Nothing about option order |
| BAMF Prüfungsordnung § 10 (3) | each candidate's sheet differs from the others' at the same exam date; nothing about option order |
| "answers sorted differently on each run" (found via web search) | App Store description of a third-party practice app, not about the exam |
| Test-taker reports (Reddit, German forums) | none found that mention option order either way; one 2021 r/AskAGerman comment asks exactly this and gets no answer |

Reading: if BAMF shuffled options, all 56 questions keeping catalog order by chance would have probability about
10^-77, and the 2008 sheet still matching the 2025 catalog shows the catalog order itself has been stable for 17
years. So the official sheets clearly print catalog order. But the 100 real sheets are not published, the rules do
not require catalog order, and sample sheets could be hand-made. Plan with the shuffled numbers (100 answers to
memorize) and treat the order-kept numbers (64) as a likely bonus.

## How much is real signal

5-fold cross-validation of a naive-Bayes scorer (correct share on questions it learned from -> on held-out ones):

- hand-made option features: 37% -> 33%
- words in the options: 51% -> 31% (mostly memorization)
- both: 56% -> 39%

So there is a real, transferable signal of about +8 to +14 points over blind guessing, mostly from: an option
repeating the question's key words (14/31 = 45%), official-channel words, values words, and numeric middle values.
Everything above that in-sample is the pool being memorized.

## Method notes

- 41 picker rules (sources: web tips, your "lowest number" idea, my own hypotheses, small fact lists, rules mined
  from the answers), every option feature, every word occurring in 3+ options, and 1,456 conditional rules.
- Precision with Wilson 95% CI, one-sided binomial p-values vs the 25% baseline, Bonferroni correction.
- Mined rules (key numbers, word lists) are derived from the answers, so they are excluded from the cross-validated
  rule list; they are really compressed facts.
- Exam model is exact (multivariate hypergeometric draw of 30/300 + 3/10, binomial for guesses), cross-checked
  against a 20,000-draw simulation (0.0071 vs 0.0069).
- Web search for existing tricks found mainly "eliminate absurd answers", "longest answer" and chancellor
  mnemonics; guides recommend studying, and the national pass rate is reported at about 96-98%.
