# scripts/non_essential

The answer-pattern study: maintained and re-runnable, but the study app and the dataset build do not need it.
Moved here from `scripts/` on 2026-10-26 (codebase review): the study is finished, its results are in
`PATTERNS.md`, `results/` and `reports/patterns_report.html`, and keeping it next to the dataset and vocabulary
builds hid which scripts the project actually depends on.

| Script | What it does | When to re-run it |
|---|---|---|
| `check_sheet_order.py` | Matches every question on the official BAMF sample sheets to the catalog and checks whether the options are printed in catalog order -> `results/sheet_order_check.json` (~30 s) | When BAMF publishes a new sample sheet or someone reports a real exam sheet (DECISIONS.md #7) |
| `mine_patterns.py` | Mines shortcut rules in the 310 questions (longest option, key words ...) with precision, cross-validation and exact pass chances -> `results/patterns.json` (~6 s) | After a new catalog version (`data/questions_bayern.json` changed) |
| `build_pattern_report.py` | Builds `reports/patterns_report.html` from the two JSON files above (~2-5 s) | After either of the scripts above ran |

`check_sheet_order.py` imports the PDF parser from `scripts/build_dataset.py`.
