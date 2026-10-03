"""Build data/translations_en.json: an English translation of every question and option, in OUR option order.

Source: the English texts of github.com/abdullahbutt/leben-in-deutschland-test (quiz-data.json, pinned commit
below). That dataset sometimes lists the options in a different order than the official catalog (e.g. Q57, Q98),
so translations are never taken by position: each of our German options is matched to the source option with
the most similar German text, and the question text is checked too. Anything without a confident one-to-one
match must be translated by hand in data/translations_en_overrides.json, otherwise the build fails.

Run:      python scripts/build_translations.py
Runtime:  ~5 s (one download of ~0.9 MB)
"""

import difflib
import itertools
import json
import logging
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "questions_bayern.json"
OVERRIDES = ROOT / "data" / "translations_en_overrides.json"
OUT = ROOT / "data" / "translations_en.json"
SOURCE_REPO = "abdullahbutt/leben-in-deutschland-test"
SOURCE_COMMIT = "0323d5d7840e2679a104ea494407e59134959ae6"   # 2026-09 ("version": "2026-09-24")
SOURCE_URL = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/quiz-data.json"
MIN_QUESTION_SIMILARITY = 0.8
MIN_OPTION_SIMILARITY = 0.75

log = logging.getLogger("build_translations")


def setup_logging() -> None:
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(),
                  logging.FileHandler(ROOT / "logs" / "build_translations.log", encoding="utf-8")],
    )


def word_bag(s: str) -> str:
    """Order-insensitive, so 'der Bundespräsident / die Bundespräsidentin' ~ 'die Bundespräsidentin/der Bundespräsident'."""
    return " ".join(sorted(re.findall(r"\w+", s.lower())))


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, word_bag(a), word_bag(b)).ratio()


def best_mapping(ours: list[str], theirs: list[str]) -> tuple[list[int], list[float]]:
    """The permutation p maximizing the summed similarity of ours[i] ~ theirs[p[i]]."""
    sims = [[similarity(a, b) for b in theirs] for a in ours]
    perm = max(itertools.permutations(range(len(theirs))), key=lambda p: sum(sims[i][p[i]] for i in range(len(ours))))
    return list(perm), [sims[i][perm[i]] for i in range(len(ours))]


def main() -> None:
    setup_logging()
    t0 = time.perf_counter()
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as resp:
        source = json.loads(resp.read().decode("utf-8"))
    by_id = {q["id"]: q for q in source["general"]}
    by_id.update({int(q["id"].split("-")[1]): q for q in source["states"]["bayern"]["questions"]})
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))["translations"] if OVERRIDES.exists() else {}
    ours = json.loads(QUESTIONS.read_text(encoding="utf-8"))

    translations, problems, reordered = {}, [], []
    for q in ours:
        key = str(q["id"])
        if key in overrides:
            translations[key] = overrides[key]
            continue
        src = by_id.get(q["id"])
        if src is None:
            problems.append(f"{key}: not in the source")
            continue
        q_sim = similarity(q["question"], src["de"])
        perm, o_sims = best_mapping(q["options"], [o["de"] for o in src["options"]])
        if q_sim < MIN_QUESTION_SIMILARITY or min(o_sims) < MIN_OPTION_SIMILARITY:
            problems.append(f"{key}: question similarity {q_sim:.2f}, option similarities {[round(s, 2) for s in o_sims]}")
            continue
        if perm != [0, 1, 2, 3]:
            reordered.append(q["id"])
        translations[key] = {"question": src["en"], "options": [src["options"][j]["en"] for j in perm]}

    if problems:
        for p in problems:
            log.error(f"needs a hand translation in {OVERRIDES.name}: {p}")
        raise SystemExit(f"{len(problems)} questions have no confident match; add them to {OVERRIDES.name}")

    for key, t in translations.items():
        if not t["question"].strip() or len(t["options"]) != 4 or not all(o.strip() for o in t["options"]):
            raise ValueError(f"question {key}: incomplete translation {t}")
    out = {
        "source": f"English texts from github.com/{SOURCE_REPO} @ {SOURCE_COMMIT[:7]}, options matched to our order by "
                  f"their German text; hand translations from {OVERRIDES.name} for {len(overrides)} questions",
        "translations": {str(q["id"]): translations[str(q["id"])] for q in ours},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info(f"{len(translations)} questions translated ({len(overrides)} by hand); options re-ordered to the "
             f"catalog order for {len(reordered)}: {reordered}")
    log.info(f"wrote {OUT.relative_to(ROOT)} in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
