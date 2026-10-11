# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "google-genai==2.28.0",
# ]
# ///
"""Build data/vocabulary_en.json: the dictionary form (with der/die/das for nouns), a short English meaning and the
word type for every row of data/vocabulary_raw.json (the words of data/vocabulary.json before rows with the same
dictionary form are merged), by Gemini 3.1 Flash-Lite on Vertex AI with one exam sentence as
context. Already translated words are kept and words no longer in the vocabulary are dropped, so a rerun only
translates new words. Hand corrections live in data/vocabulary_en_overrides.json and are applied on top every run
(an override for an unknown word fails the run).

Needs: Google application-default credentials (gcloud auth application-default login) for the Vertex project in
.env (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION). Every call is appended to the cost ledger videos/build/costs.json.

Run:      uv run scripts/translate_vocabulary.py          (add --one to translate a single batch as a check)
Runtime:  ~2 min for all ~1,400 words (29 calls of 50 words), seconds when nothing is new
Cost:     ~$0.07 for all words (measured cost is logged at the end)
"""

import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "data" / "vocabulary_raw.json"   # rows before the same-form merge (scripts/build_vocabulary.py)
QUESTIONS = ROOT / "data" / "questions_bayern.json"
OUT = ROOT / "data" / "vocabulary_en.json"
OVERRIDES = ROOT / "data" / "vocabulary_en_overrides.json"
LEDGER = ROOT / "videos" / "build" / "costs.json"
MODEL = "gemini-3.1-flash-lite"
PRICE_IN, PRICE_OUT = 0.25e-6, 1.50e-6   # $/token (thinking tokens count as output), ai.google.dev/gemini-api/docs/pricing (read 2026-10-06); Vertex assumed equal
BATCH = 50
TYPES = ["noun", "verb", "adjective", "adverb", "function"]
PROMPT = """You are writing a German-English vocabulary list for an adult learner preparing for the German citizenship test (Einbürgerungstest).
For each item you get: key, the word as found by a lemmatizer, whether the lemmatizer saw a function word or a content word, and one exam sentence where it occurs.
Return for every item:
- "de": the correct German dictionary form. Nouns: singular with the definite article ("die Wahl", "der Bundestag"; plural-only nouns with "die", e.g. "die Eltern"). Verbs: infinitive. Adjectives/adverbs: base form. Fix lemmatizer mistakes (e.g. "Kürbiß" -> "der Kürbis", "Nachtruh" -> "die Nachtruhe", "muss" -> "müssen").
- "en": a short English meaning that fits the exam sentence, at most 5 words, no article for nouns. If the word has a second common meaning a learner will meet (e.g. "sie" also "Sie" = you), add it after a semicolon.
- "type": the word type as used in the sentence: noun, verb (including modal and auxiliary verbs), adjective (also when used after "sein", e.g. "ist wichtig"), adverb, or function (articles, pronouns, prepositions, conjunctions, particles, numerals).
Return a JSON array with exactly one object {"key", "de", "en", "type"} per input item, keys copied exactly."""

log = logging.getLogger("translate_vocabulary")


def setup_logging() -> None:
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(),
                  logging.FileHandler(ROOT / "logs" / "translate_vocabulary.log", encoding="utf-8")],
    )


def example_sentence(word: dict, texts: dict[int, list[str]]) -> str:
    """The first question or option text of the word's questions that contains one of its forms as a whole word."""
    for qid in word["questions"]:
        for t in texts[qid]:
            if any(re.search(rf"(?<!\w){re.escape(f)}(?!\w)", t) for f in word["forms"]):
                return t[:160]
    raise RuntimeError(f"no example sentence found for {word['key']}")


def save(done: dict) -> None:
    OUT.write_text(json.dumps({"description": f"Dictionary form, English meaning and word type for data/vocabulary.json, by {MODEL} "
                                              "(scripts/translate_vocabulary.py) plus hand corrections from data/vocabulary_en_overrides.json. "
                                              "Machine translation: spot-checked, not reviewed word by word.",
                               "words": done}, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    setup_logging()
    t0 = time.time()
    env = dict(l.strip().split("=", 1) for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
    client = genai.Client(vertexai=True, project=env["GOOGLE_CLOUD_PROJECT"], location=env["GOOGLE_CLOUD_LOCATION"])
    words = json.loads(VOCAB.read_text(encoding="utf-8"))["words"]
    keys = {w["key"] for w in words}
    texts = {q["id"]: [q["question"], *q["options"]] for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}
    done = json.loads(OUT.read_text(encoding="utf-8"))["words"] if OUT.exists() else {}
    stale = [k for k in done if k not in keys]
    for k in stale:
        del done[k]
    save(done)   # also when nothing new is translated: stale entries would make the app refuse to start
    if stale:
        log.info(f"dropped {len(stale)} translations of words no longer in the vocabulary: {stale[:10]}")
    todo = [w for w in words if w["key"] not in done]
    if "--one" in sys.argv:
        todo = todo[:BATCH]
    log.info(f"{len(words)} words, {len(done)} already translated, {len(todo)} to do in {-(-len(todo) // BATCH)} calls")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else []
    schema = types.Schema(type="ARRAY", items=types.Schema(type="OBJECT", required=["key", "de", "en", "type"], properties={
        "key": types.Schema(type="STRING"), "de": types.Schema(type="STRING"), "en": types.Schema(type="STRING"),
        "type": types.Schema(type="STRING", enum=TYPES)}))
    spent = 0.0
    for b in range(0, len(todo), BATCH):
        batch = todo[b: b + BATCH]
        items = [{"key": w["key"], "word": w["lemma"], "seen_as": w["key"].split("|")[1], "sentence": example_sentence(w, texts)} for w in batch]
        r = client.models.generate_content(model=MODEL, contents=PROMPT + "\n\nItems:\n" + json.dumps(items, ensure_ascii=False),
                                           config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema, temperature=0))
        out = json.loads(r.text)
        got = {o["key"]: o for o in out}
        want = {w["key"] for w in batch}
        if set(got) != want or len(out) != len(batch) or any(not o["de"].strip() or not o["en"].strip() or o["type"] not in TYPES for o in out):
            raise RuntimeError(f"batch {b // BATCH + 1}: bad answer, missing {sorted(want - set(got))[:5]}, extra {sorted(set(got) - want)[:5]}")
        for k, o in got.items():
            done[k] = {"de": o["de"].strip(), "en": o["en"].strip(), "type": o["type"]}
        u = r.usage_metadata
        out_tokens = (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
        cost = u.prompt_token_count * PRICE_IN + out_tokens * PRICE_OUT
        spent += cost
        ledger.append({"at": datetime.now().isoformat(timespec="seconds"), "model": MODEL, "api": "vertex", "purpose": "translate_vocabulary",
                       "prompt_tokens": u.prompt_token_count, "output_tokens": u.candidates_token_count,
                       "thoughts_tokens": u.thoughts_token_count or 0, "cost_usd_if_paid": round(cost, 5)})
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
        save(done)
        n, elapsed = b + len(batch), time.time() - t0
        log.info(f"{n}/{len(todo)} words, {elapsed:.0f}s elapsed, ~{elapsed / n * (len(todo) - n):.0f}s left, ${spent:.4f} so far")

    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))["words"]
    unknown = [k for k in overrides if k not in keys]
    if unknown:
        raise RuntimeError(f"data/vocabulary_en_overrides.json has words that are not in the vocabulary: {unknown}")
    for k, fix in overrides.items():
        bad = set(fix) - {"de", "en", "type"}
        if bad or ("type" in fix and fix["type"] not in TYPES):
            raise RuntimeError(f"override {k}: unknown fields {bad} or type {fix.get('type')!r}")
        done[k] = {**done.get(k, {}), **fix}
    save(done)
    missing = [w["key"] for w in words if w["key"] not in done or set(done[w["key"]]) != {"de", "en", "type"}]
    if missing and "--one" not in sys.argv:
        raise RuntimeError(f"{len(missing)} words without a complete translation: {missing[:10]}")
    log.info(f"done: {len(done)} words, {len(overrides)} hand overrides applied, this run cost ${spent:.4f} (if paid), took {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
