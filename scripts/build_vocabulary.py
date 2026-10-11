# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "spacy==3.8.16",
#     "de_core_news_md @ https://github.com/explosion/spacy-models/releases/download/de_core_news_md-3.8.0/de_core_news_md-3.8.0-py3-none-any.whl",
# ]
# ///
"""Build data/vocabulary.json: every distinct German word (dictionary form) in the 310 questions and all options.

Words are lemmatized with spaCy's German model, so "wählt" and "gewählt" count once as "wählen". Names and places
(people, cities, countries, states) and all-caps abbreviations (CDU, DDR, ...) are counted separately, not as
vocabulary. The model's name detection marks many ordinary nouns as names (Staat, Stadt, Frau, Synagoge, ...);
NOT_A_NAME below is the hand-checked list that puts them back. Feminine forms (Bürgerin, Ärztin, Auswanderin) are
merged into the base word, because the catalog prints both everywhere and "-in" is learned once as a rule.

spaCy only decides "function word" vs "content word" here; the word type shown in the app (noun, verb, adjective,
adverb, function) comes from data/vocabulary_en.json (scripts/translate_vocabulary.py), which sees the word in
context and corrects spaCy's tags (it files "der" under adverbs, predicative adjectives under adverbs, modal verbs
under auxiliaries). When that file exists, words the translator gave the same dictionary form are merged
(muss/müssen, alle/aller). Full rebuild: build, translate, build again, translate again (only prunes).

Run:      uv run scripts/build_vocabulary.py
Runtime:  ~15 s (first run also downloads the ~40 MB model)
"""

import json
import logging
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import spacy

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "questions_bayern.json"
TRANSLATIONS = ROOT / "data" / "vocabulary_en.json"
RAW = ROOT / "data" / "vocabulary_raw.json"   # rows before the same-form merge: what gets translated
OUT = ROOT / "data" / "vocabulary.json"
FUNCTION_POS = {"DET", "ADP", "PRON", "CCONJ", "SCONJ", "PART", "NUM"}
CONTENT_KIND = {"NOUN": "noun", "PROPN": "noun", "VERB": "verb", "AUX": "verb", "ADJ": "adjective", "ADV": "adverb"}
KINDS = {"noun", "verb", "adjective", "adverb", "function", "other"}
# Ordinary words the model tags as names or places (checked by hand 2026-10-11 against its full list).
NOT_A_NAME = {
    "Staat", "Staaten", "Bundesrepublik", "Bundesverfassungsgericht", "Bundesverfassungsgerichtes", "deutsche", "Deutsche",
    "Straße", "Republik", "Pressezensur", "Bundesstaat", "Schloss", "Volksgesetz", "rechtsstaatlich", "Fürstentum", "Löwe",
    "Adler", "Bär", "Sozialabgaben", "Spendengeldern", "Staatenbund", "Völker", "Bundestagssitz", "Bundesratsgebäude",
    "Auswärtiges", "Amt", "Oststaat", "Bund", "Bundesgerichtshof", "Oberlandesgericht", "Verwaltungsgericht",
    "Bundesminister", "Wohngeld", "Bundesadler", "Dreiklassenwahlrecht", "Zulassungsgrenze", "Kanzlerinnen",
    "Ministerpräsidentinnen", "Gerichtsschöffin", "Mauerbaus", "demokratischen", "Reich", "Reichstagsgebäudes",
    "Wehrmacht", "Landtransport", "Basilika", "Synagoge", "Zionistenkongresses", "Ährenkranz", "kommunistischen",
    "Kapitalismus", "Europabündnis", "Stadt", "Euro", "Frau", "Schulabschluss", "Behördenleiterin", "Vereinstrainerin",
    "Bibliotheksaufsicht", "Allerheiligen", "Freistaat", "Welches", "Landtag", "in", "Finanzministerin",
    "Finanzminister", "Bündnis", "Bundes",
}
# Adjectives that are part of names (Warschauer Pakt, Schengener Abkommen, Römische Verträge, ...).
PLACE_ADJECTIVES = {"hamburger", "londoner", "römisch", "römischen", "schengener", "warschauer", "süddeutsch", "pariser"}
# Surface forms whose spaCy lemma is wrong (review 2026-10-11): führen -> fahren, was -> wer, mich/mir -> sich, ...
LEMMA_OVERRIDES = {"führen": "führen", "was": "was", "mich": "ich", "mir": "ich", "selben": "selbe", "trainiere": "trainieren", "erster": "erster", "unterste": "unterster",
                   # the possessive "sein" (his) is a different word from the verb "sein" (to be)
                   "seine": "seine", "seinem": "seine", "seinen": "seine", "seiner": "seine", "seines": "seine"}
MINORITY = 0.15   # a stray function/content tag below this share of a word's uses is merged into the majority

log = logging.getLogger("build_vocabulary")


def setup_logging() -> None:
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(),
                  logging.FileHandler(ROOT / "logs" / "build_vocabulary.log", encoding="utf-8")],
    )


def texts(questions: list[dict]) -> list[tuple[int, str, str]]:
    """(question id, 'question' | 'answer' | 'option', text) without photo credits."""
    out = []
    for q in questions:
        out.append((q["id"], "question", re.sub(r"©.*", "", q["question"])))
        for i, o in enumerate(q["options"]):
            out.append((q["id"], "answer" if i == q["answer_index"] else "option", o))
    return out


def de_umlaut_last(s: str) -> str:
    plain = {"ä": "a", "ö": "o", "ü": "u", "Ä": "A", "Ö": "O", "Ü": "U"}
    for i in range(len(s) - 1, -1, -1):
        if s[i] in plain:
            return s[:i] + plain[s[i]] + s[i + 1:]
    return s


class Groups:
    """Union-find over word keys; the representative is the more frequent key."""

    def __init__(self, count: Counter):
        self.count = count
        self.parent = {k: k for k in count}

    def find(self, k):
        while self.parent[k] != k:
            self.parent[k] = self.parent[self.parent[k]]
            k = self.parent[k]
        return k

    def union(self, a, b, keep_b: bool = False) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if keep_b:
            keep, drop = rb, ra
        else:
            keep, drop = (ra, rb) if (self.count[ra], -len(ra[0])) >= (self.count[rb], -len(rb[0])) else (rb, ra)
        self.parent[drop] = keep
        self.count[keep] += self.count[drop]
        return True

    def members(self) -> dict:
        out = defaultdict(list)
        for k in self.parent:
            out[self.find(k)].append(k)
        return out


def main() -> None:
    setup_logging()
    t0 = time.time()
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    nlp = spacy.load("de_core_news_md")
    items = texts(questions)
    count, kinds, forms, where, places = Counter(), defaultdict(Counter), defaultdict(set), defaultdict(set), defaultdict(set)
    names, abbreviations = Counter(), Counter()
    for (qid, place, _), doc in zip(items, nlp.pipe(t for _, _, t in items)):
        for tok in doc:
            if not tok.is_alpha:
                continue
            text = tok.text
            if len(text) >= 2 and (text.isupper() or text == "AfD"):
                abbreviations[text] += 1
                continue
            if (tok.pos_ == "PROPN" or tok.ent_type_ in ("PER", "LOC")) and text not in NOT_A_NAME:
                names[text] += 1
                continue
            lemma = LEMMA_OVERRIDES.get(text.lower()) or (tok.lemma_ if tok.pos_ in ("NOUN", "PROPN") else tok.lemma_.lower())
            if lemma.lower() in PLACE_ADJECTIVES:
                names[text] += 1
                continue
            group = "function" if tok.pos_ in FUNCTION_POS else "content"
            key = (lemma, group)
            count[key] += 1
            kinds[key]["function" if group == "function" else CONTENT_KIND.get(tok.pos_, "other")] += 1
            forms[key].add(text)
            where[key].add(qid)
            places[key].add(place)
    log.info(f"{sum(count.values())} words counted, {len(count)} lemma keys")

    g = Groups(Counter(count))
    # 1. a lemma tagged both as function and content word: a small minority is a tagging slip (der tagged ADV once)
    by_lemma = defaultdict(list)
    for k in count:
        by_lemma[k[0]].append(k)
    slips = 0
    for keys in by_lemma.values():
        if len(keys) == 2:
            small, big = sorted(keys, key=lambda k: count[k])
            if count[small] < MINORITY * (count[small] + count[big]):
                slips += g.union(small, big)
    # 2. feminine forms -> base noun (Bürgerin -> Bürger, Ärztin -> Arzt, Auswanderin -> Auswanderer, Gerichtsschöffin -> Gerichtsschöffe)
    nouns = {k[0]: k for k in count if kinds[k].most_common(1)[0][0] == "noun"}
    feminine = glitches = 0
    for n, k in list(nouns.items()):
        for suf in ("innen", "inne", "inn", "in"):
            if n.endswith(suf) and len(n) - len(suf) >= 3:
                stem = n[: -len(suf)]
                base = next((c for c in (stem, de_umlaut_last(stem), stem + "er", stem + "e") if c in nouns and c != n), None)
                if base:
                    feminine += g.union(k, nouns[base], keep_b=True)   # the base word names the row
                break
        # 3. lemma glitches: Volke/Volk, Kindergart/Kindergarten
        for suf in ("en", "e", "n", "s"):
            if n.endswith(suf) and len(n) - len(suf) >= 3 and n[: -len(suf)] in nouns:
                glitches += g.union(k, nouns[n[: -len(suf)]])
    # The rows so far do not depend on translations; they are what scripts/translate_vocabulary.py translates. Keeping
    # them separate makes the same-form merge below stable: a merged row keeps its own translation on every rebuild.
    raw = []
    for rep, members in g.members().items():
        raw.append({"key": f"{rep[0]}|{rep[1]}", "lemma": rep[0], "forms": sorted(set().union(*(forms[m] for m in members))),
                    "questions": sorted(set().union(*(where[m] for m in members)))})
    raw.sort(key=lambda w: w["key"])
    RAW.write_text(json.dumps({"description": "Rows of scripts/build_vocabulary.py before words with the same dictionary form are merged; "
                                              "input of scripts/translate_vocabulary.py.", "words": raw}, ensure_ascii=False, indent=1), encoding="utf-8")
    # 4. words the translator gave the same dictionary form (muss / müssen / mussn, alle / aller)
    translations = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))["words"] if TRANSLATIONS.exists() else {}
    same_form = 0
    by_de = defaultdict(list)
    for rep in list(g.members()):
        t = translations.get(f"{rep[0]}|{rep[1]}")
        if t:
            by_de[t["de"].strip()].append(rep)   # also across function/content: "wie" is one word to learn
    for reps in by_de.values():
        for other in reps[1:]:
            same_form += g.union(reps[0], other)
    groups = g.members()
    log.info(f"merged: {slips} function/content tagging slips, {feminine} feminine forms, {glitches} lemma glitches, "
             f"{same_form} same dictionary form ({'translations found' if translations else 'no translations yet'}) -> {len(groups)} words")

    words, provisional = [], 0
    for rep, members in groups.items():
        key = f"{rep[0]}|{rep[1]}"
        t = translations.get(key)
        if t:
            kind = t["type"]
        else:
            provisional += 1
            kind = sum((kinds[m] for m in members), Counter()).most_common(1)[0][0]
        if kind not in KINDS:
            raise RuntimeError(f"{key}: unknown word type {kind!r}")
        words.append({"key": key, "lemma": rep[0], "kind": kind, "count": sum(count[m] for m in members),
                      "forms": sorted(set().union(*(forms[m] for m in members))),
                      "questions": sorted(set().union(*(where[m] for m in members))),
                      "core": bool(set().union(*(places[m] for m in members)) & {"question", "answer"})})
    words.sort(key=lambda w: (-w["count"], w["lemma"].lower()))
    if len({w["key"] for w in words}) != len(words):
        raise RuntimeError("duplicate word keys after merging")

    result = {
        "description": "Distinct German words (dictionary forms) in the 310 questions + all options, built by scripts/build_vocabulary.py "
                       "(spaCy de_core_news_md 3.8.0; word types from data/vocabulary_en.json). Names/places and abbreviations are not "
                       "vocabulary. 'core' = the word appears in a question or a correct answer. Automatic lemmatization: counts are "
                       "approximate (about +-5%). The key of a word is the key of its most frequent row in data/vocabulary_raw.json.",
        "names_and_places_excluded": len(names),
        "abbreviations_excluded": sorted(abbreviations),
        "words": words,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info(f"wrote {OUT.relative_to(ROOT)}: {len(words)} words ({dict(Counter(w['kind'] for w in words))}), "
             f"{sum(w['core'] for w in words)} core, {provisional} with a provisional spaCy word type (translate them next), "
             f"{len(names)} names/places and {len(abbreviations)} abbreviations excluded, in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
