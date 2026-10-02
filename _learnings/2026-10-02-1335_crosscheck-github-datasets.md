# Cross-check of our answers against GitHub datasets: one agrees fully, the popular Anki deck is stale

Compared `data/questions_bayern.json` (310 Bayern questions) with two third-party datasets by
(section, catalog number), answers compared as sorted word lists.

```
youssefeghaly: compared 310, disagreements 0
vlad-ds: compared 310, disagreements 10
   (('general', 14), 'meine Meinung in Leserbriefen äußern kann.', 'meine Meinung im Internet äußern kann.')
   (('general', 21), 'Bild 3', 'Bild 1')
   (('general', 72), 'Olaf Scholz', 'Friedrich Merz')
   (('general', 73), 'CDU/CSU und SPD.', 'CDU/CSU und AfD.')
   (('general', 127), 'die kleinen Parteien nicht so viel Geld haben, ...', 'viele kleine Parteien die Regierungsbildung erschweren.')
   (('general', 136), 'ungerechtigter Kündigung ...', 'ungerechtfertigter Kündigung ...')
   (('general', 175), '6', '4')
   (('general', 209), 'Bild 3', 'Bild 4')
   (('general', 226), 'Bild 3', 'Bild 2')
   (('Bayern', 4), '16', '18')
```
(first value = vlad-ds, second = ours)

Resolution, each checked by hand:
- 14: question was revised (new distractor about Nazi/Hamas/IS symbols); old deck has the old options.
- 72, 73: changed with the 2025 federal election (Merz chancellor; CDU/CSU and AfD are the two largest factions).
- 127, 175: deck is plainly wrong (4 occupation zones; the 5% hurdle exists because many small parties make forming a government hard).
- 136: typo in the deck only, same answer.
- 21, 209, 226: looked at the official images - federal eagle is 1, GDR emblem is 4, EU flag is 2. The deck says "Bild 3" for all three, probably a parsing bug.
- Bayern 4: local-election voting age in Bayern is 18 (Bayern did not lower it to 16).

Notes: youssefeghaly's file says its answer key comes from the leben-in-deutschland project
(MIT), which derives it independently of our OET scrape, so the 310/310 match is real corroboration.
The vlad-ds CSV uses `:` as the field separator (default `csv.reader` reads 0 rows).
Probe script was throwaway (scratchpad), not committed.
