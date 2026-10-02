# BAMF Online-Testcenter: answers are in the DOM, stems are images, 12 stems missing

**Symptom**
The official PDF catalog has no answer key. The Online-Testcenter (oet.bamf.de, APEX app 514) shows
the answers only after you click one.

**Cause / findings**
- The correct option is already in the HTML before any click: its radio button has `id="FARBE"`
  (and its cells `name="FARBE"`); the onclick paints `FARBE` green. Options are plain text in
  `td[headers=ANTWORT]`.
- The question stem is a PNG (`#P30_AUFGABENSTELLUNG_BILD img`, `show_pag_bild` process). Text-only
  stems are ~1-2 KB, picture questions 40-130 KB - that size gap is how `build_dataset.py` detects
  picture questions (threshold 6000 bytes).
- For 12 questions the page has no stem image at all, only an internal ID in `#P30_BESCHREIBUNG`,
  e.g. Q14 `ET2021a_Meinungsfreiheit`, Q288 `ET1131e_Verantwortung_Israel`. Affected:
  `[14, 59, 66, 96, 111, 118, 149, 182, 184, 206, 234, 288]`. Anyone practicing on the official site
  sees four answers and no question for these.
- The OET wording differs cosmetically from the 2025 PDF: male-first gender pairs with spaces
  ("der Bundespräsident / die Bundespräsidentin") vs PDF female-first ("die Bundespräsidentin/der
  Bundespräsident"), and picture options "1".."4" vs "Bild 1".."Bild 4". Option ORDER is the same.
- Navigation: "nächste Aufgabe" is a form POST (`htmldb_goSubmit('GET_NEXT_ID')`); the
  "Gehe zu Aufgabe Nr." dropdown `#P30_ROWNUM` jumps directly. ~1.1 s per question.
- The APEX session expires after ~20 min idle: `selectOption('#P30_ROWNUM', ...)` then never navigates
  (30 s timeout). Fix: start again from `f?p=514:1:0`.

**Playwright MCP gotchas hit along the way**
- `browser_run_code_unsafe` has no `fs`/`require`/dynamic `import`. To get data out, park it in
  `window.__oet` and dump it with `browser_evaluate(..., filename=...)`.
- `filename` may only point inside the repo or `.playwright-mcp/` (scratchpad paths are refused).
- The dumped file is a JSON string wrapped in JSON (double-encoded) - `json.loads` twice.
- A 105-question batch takes ~150 s and gets moved to the background after 120 s; that is fine,
  the completion notification arrives.
