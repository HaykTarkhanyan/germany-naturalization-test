# The English source dataset rewrites questions and reorders options - match by German text, never by position

**Symptom**
abdullahbutt/leben-in-deutschland-test numbers its questions like the official catalog (id 1-300 + "bayern-301"),
so taking its English by id and option index looked safe. Comparing its German with ours
(`data/questions_bayern.json`, from the BAMF PDF + Online-Testcenter):

```
general: question text equal 230/300, options equal+same order 219/300
exact 253, near 19, flagged 38   (after word-bag matching of question and options)
```

**Cause**
- Options in a different order than the catalog for 19 questions, e.g. Q57 (options C/D swapped) and Q98
  (A/B swapped). Index-based English would have shown the wrong translation under those options.
- For 38 questions the German is not the official text at all. Examples (ours vs theirs):
  - Q247 "Wie heißt dieser Schutz?" (answer Mutterschutz) vs "Wie lange dauert die gesetzliche Mutterschutzfrist ...?"
    with the option changed to "Mutterschutz (8 Wochen nach der Geburt)".
  - Q255 "Bei Erziehungsproblemen können Eltern ... Hilfe erhalten vom ..." vs "Welche Behörde ist zuständig, wenn
    Kinder in Deutschland misshandelt werden?"
  - Q267 (22-year-old daughter lives with her boyfriend) vs "Die 19-jährige Tochter möchte von zu Hause ausziehen".
  - Q251 "Wenn man ... ein Kind schlägt" vs "Wenn ein Mann ... sein Kind schlägt" (passed the similarity threshold;
    caught in the manual review of near matches).

**Consequences**
- `scripts/build_translations.py` maps each of our options to the source option with the most similar German
  (best permutation), checks the question similarity (>= 0.8) and fails unless every unmatched question has a hand
  translation in `data/translations_en_overrides.json` (40 entries).
- The vlad-ds Anki deck had wrong answers (see 2026-10-02-1335); this one has rewritten questions. Third-party
  question datasets are not interchangeable with the official catalog - always diff against it first.
