# Official sample sheets keep the catalog's option order - real exam sheets are unverified

Position-based habits ("pick B when unsure") only matter if the printed exam lists options in catalog order.

**Evidence** (`scripts/check_sheet_order.py` -> `results/sheet_order_check.json`): both official BAMF sample sheets,
matched question by question to the current catalog (all 460 questions) by their option sets:

```
musterbogen_einbuergerungstest.pdf (Bayern, Prüfungsnr. 105498, Dec 2021): checkable 30, same order 30, different 0
musterbogen_einbuergerungstest_2008_berlin.pdf (Berlin, Prüfungsnr. 1, 2008): checkable 26, same order 26, different 0
total: 56/56 matched questions in catalog order; if shuffled, chance of that = 10^-77
```

The 2008 sheet was on bamf.de until ~2021 (Wayback CDX: `musterbogen_einbuergerungstest.pdf?__blob=publicationFile&v=4`,
captured 2020-10-29; byte-identical copy at innen.hessen.de/.../2021-06/bamf-testfragebogen.pdf). The current Bayern
sheet is v=8. Those are the only two official sheets found.

**Caveat - why this is not proof for the real exam:**
- EinbTestV § 1 (2), verbatim: "Die aus dem Fragenkatalog in Anlage 1 erstellten 100 Fragebögen enthalten 33 Fragen,
  darunter jeweils drei aus den Fragen, die sich auf das Bundesland beziehen ... Die Fragebögen werden nicht
  veröffentlicht." No word on option order; neither in the BAMF Prüfungsordnung.
- Sample sheets could be built by hand for publication.
- No test-taker report found (Reddit, German forums) that mentions option order either way. The only "answers are
  sorted differently on each run" claim found is from an App Store description of a third-party practice app.

**Disproven earlier claim:** this file was first titled "The paper exam keeps the catalog's option order", based on
one sheet. The user rightly questioned it; the claim is now limited to the official sample sheets.

**Consequence for the strategy** (`results/patterns.json`): if options are shuffled, the content rules still cut the
answers to memorize for a 95% pass chance from 148 to 100; the B/D/A/C fallback brings it to 64 only if order is kept.
