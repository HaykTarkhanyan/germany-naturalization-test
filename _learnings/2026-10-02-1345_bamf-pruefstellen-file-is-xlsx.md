# BAMF "Prüfstellen" download is an Excel file, not a PDF

BAMF's per-state test-center lists follow the usual download URL pattern
`.../Einbuergerung/Pruefstellen-BY.pdf?__blob=publicationFile`, but the file served is an `.xlsx`
(`file` says "Microsoft Excel 2007+"; `pdfinfo` fails with "Couldn't find trailer dictionary").
Saved as `official/Pruefstellen-BY.xlsx`. Read it with `openpyxl` (sheet "Tabelle1", header in row 2:
Kreis / PLZ / Ort / Name der Prüfstelle / Straße / Telefon / E-Mail).

Some rows carry a `*` in the first column ("Spalte 1"); the sheet has no legend for it.

The third-party copy in leben-in-deutschland's `prüfstellen.json` is stale for Munich (lists
"Hilfe von Mensch zu Mensch" which is not on the official list, misses Bildungsinstitut Kavalchuk,
and has an old MAS address).
