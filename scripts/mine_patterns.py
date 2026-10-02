"""Mine shortcut rules ("patterns") in the 310 Bayern questions and measure how well they work.

Reads data/questions_bayern.json and writes results/patterns.json - the record. The HTML report is built
from that JSON by scripts/build_pattern_report.py, so the report can be rebuilt without rerunning this.

What it measures:
  - picker rules (pick one option, e.g. "the longest option"): support, precision, lift over the 25% of a
    blind guess, net gain (hits - misses), Wilson 95% CI, one-sided binomial p-values, Bonferroni flag
  - option features (e.g. "option contains 'nur'"): P(correct | feature) vs the 25% baseline, i.e. which
    options you can cross out
  - data-mined word weights and a naive-Bayes combination of all features, with 5-fold cross-validation
    to separate real patterns from noise
  - single-word rules ("options with 'Polizei' are never right") and conditional rules ("if the question
    contains X, the longest option is right"), each re-mined on training folds and scored on held-out folds
  - a greedy decision list a human could memorize, plus exact exam pass probabilities
    (30 of 300 general + 3 of 10 Bayern drawn, 17 of 33 to pass) and how many questions you still
    have to memorize with and without the rules

Run:      uv run python scripts/mine_patterns.py
Runtime:  ~6 s (measured on this laptop; was 106 s before caching per-question results)
"""

import json
import logging
import math
import random
import re
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "questions_bayern.json"
OUT = ROOT / "results" / "patterns.json"

SEED = 509
BASELINE = 0.25            # blind guess, 4 options
K_FOLDS = 5
MIN_SUPPORT = 5            # a rule must fire on at least this many questions to enter the decision list
MIN_LIST_PRECISION = 0.5   # ... and be right at least this often (2x the blind-guess rate)
MIN_TOKEN_SUPPORT = 4      # a word must occur in at least this many options to get a weight
EXAM = {"general": (300, 30), "Bayern": (10, 3)}   # pool size, questions drawn
PASS_MARK = 17
PASS_TARGETS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]   # P(pass) levels for "how many answers to memorize"
ALPHA = 0.05

(ROOT / "logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "mine_patterns.log", encoding="utf-8")],
)
log = logging.getLogger("mine_patterns")

STOPWORDS = set("""
der die das den dem des ein eine einen einem einer eines und oder aber in im ins ist sind war waren wird werden
wurde wurden zu zum zur mit von vom für auf an am als auch es sie er ihr ihre ihren ihrem ihrer sein seine seinen
seinem seiner man wer was wie wo wann warum welche welcher welches welchen welchem nicht kein keine keinen keiner
keinem sich dass bei aus nach vor über unter durch hat haben hatte kann können muss müssen darf dürfen soll sollen
gibt gilt dieser diese dieses diesen diesem so nur noch schon sehr mehr hier dort deutschland deutschen deutsche
deutscher bundesrepublik heißt nennt
""".split())

# Lexicons: "x*" = word starts with x, "*x" = word ends with x, otherwise the exact word.
LEXICONS = {
    "absolute": ("absolute words (nur, immer, nie, alle, sofort, ...)",
                 ["nur", "immer", "nie", "niemals", "alle", "allen", "jede*", "ausschließlich", "sofort", "nichts",
                  "muss", "müssen", "überall", "gar"]),
    "hedge": ("hedging words (kann, meistens, oft, in der Regel, auch, ...)",
              ["kann", "können", "könnte", "meist*", "oft", "häufig", "regel", "grundsätzlich", "möglich*", "auch",
               "manchmal", "teilweise"]),
    "values": ("democratic-values words (Freiheit, gleich, Würde, Demokratie, Grundgesetz, ...)",
               ["frei*", "*freiheit", "gleich*", "demokrat*", "würde", "*würde", "frieden*", "toleran*", "schutz",
                "schütz*", "rechtsstaat*", "grundgesetz*", "verfassung*", "menschenrecht*", "solidar*"]),
    "violence": ("violence / coercion words (Gewalt, schlagen, Waffe, zwingen, bedrohen, ...)",
                 ["gewalt*", "schlag*", "schläg*", "geschlagen", "waffe*", "töt*", "prügel*", "schieß*", "zwing*",
                  "gezwungen", "droh*", "bedroh*", "bestech*", "rache", "angriff*", "zerstör*", "beleidig*",
                  "beschimpf*"]),
    "absurd_power": ("monarchy / dictatorship / military words (König, Kaiser, Diktatur, Militär, ...)",
                     ["könig*", "kaiser*", "diktat*", "führer*", "militär*", "armee*", "soldat*", "papst", "fürst*",
                      "adel*"]),
    "do_nothing": ("'do nothing / ignore it' words (nichts, ignorieren, egal, wegwerfen, liegen lassen)",
                   ["nichts", "ignor*", "egal", "wegwerf*", "liegen"]),
    "legal_remedy": ("legal-remedy / official-channel words (Einspruch, Widerspruch, Gericht, Behörde, Beratung)",
                     ["einspruch", "widerspruch", "klage*", "gericht*", "anwalt*", "beratung*", "behörde*", "antrag",
                      "beschwerde*"]),
    "money": ("money words (Geld, bezahlen, Euro, Steuer, ...)",
              ["geld*", "bezahl*", "zahl*", "euro", "steuer*", "kosten*"]),
    "police": ("the police (Polizei)", ["polizei*"]),
}

# Options with these features get crossed out before the decision list falls back to a default position.
# Chosen from the option-feature table: each is correct far less often than the 25% of a random option.
CROSS_OUT = ["lex_do_nothing", "lex_police", "num_lowest", "option_negated"]
MIN_WORD_SUPPORT = 3       # mined single-word rules: the word must occur in at least this many options

EAST_STATES = {"brandenburg", "sachsen", "sachsen-anhalt", "thüringen", "mecklenburg-vorpommern"}
NEIGHBORS = {"dänemark", "polen", "tschechien", "österreich", "schweiz", "frankreich", "luxemburg", "belgien",
             "niederlande"}


# ----------------------------------------------------------------------------- text helpers

def words(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower())


def content_words(s: str) -> set[str]:
    return {w for w in words(s) if w not in STOPWORDS and (len(w) > 2 or w.isdigit())}


def matches_lexicon(text: str, entries: list[str]) -> bool:
    for w in words(text):
        for e in entries:
            if e.endswith("*") and w.startswith(e[:-1]):
                return True
            if e.startswith("*") and w.endswith(e[1:]) and w != e[1:]:
                return True
            if w == e:
                return True
    return False


def echo_overlap(question: str, option: str) -> int:
    """Content words of the option that also occur in the question (prefix match, so Haut ~ Hautfarbe)."""
    qw = content_words(question)
    return sum(1 for w in content_words(option)
               if any((v.startswith(w) or w.startswith(v)) and min(len(v), len(w)) >= 4 for v in qw))


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def memo_by_qid(fn):
    """Cache a per-question function by question id (CV and the greedy list call each rule thousands of times)."""
    cache = {}

    def wrapped(q):
        if q["id"] not in cache:
            cache[q["id"]] = fn(q)
        return cache[q["id"]]
    return wrapped


def unique_argmax(values: list[float]) -> int | None:
    """Index of the single largest value; None on a tie (the rule abstains)."""
    best = max(values)
    idx = [i for i, v in enumerate(values) if v == best]
    return idx[0] if len(idx) == 1 else None


def prepare(r: dict) -> dict:
    q = dict(r)
    opts = r["options"]
    q["picture_only"] = all(re.fullmatch(r"(Bild )?\d", o) for o in opts)
    q["negated"] = bool(re.search(r"\b(nicht|kein\w*)\b", r["question"], re.I))
    templates = {re.sub(r"\d+(?:[.,]\d+)?", "#", o).strip(" .") for o in opts}
    nums = [re.findall(r"\d+(?:,\d+)?", o) for o in opts]
    q["numeric"] = (not q["picture_only"] and r["image"] is None and len(templates) == 1 and all(nums))
    q["num_values"] = [float(n[0].replace(",", ".")) for n in nums] if q["numeric"] else None
    return q


# ----------------------------------------------------------------------------- picker rules

def rule_longest(q):
    return unique_argmax([len(o) for o in q["options"]])


def rule_shortest(q):
    return unique_argmax([-len(o) for o in q["options"]])


def rule_longest_words(q):
    return unique_argmax([len(words(o)) for o in q["options"]])


def rule_odd_length(q):
    lens = [len(o) for o in q["options"]]
    mean = sum(lens) / 4
    return unique_argmax([abs(x - mean) for x in lens])


def make_position(k):
    return lambda q: k


def make_numeric_rank(rank):
    """0 = lowest, 1 = second lowest, 2 = second highest, 3 = highest."""
    def rule(q):
        if not q["numeric"] or len(set(q["num_values"])) != 4:
            return None
        return sorted(range(4), key=lambda i: q["num_values"][i])[rank]
    return rule


def rule_echo(q):
    ov = [echo_overlap(q["question"], o) for o in q["options"]]
    return unique_argmax(ov) if max(ov) > 0 else None


def rule_anti_echo(q):
    ov = [echo_overlap(q["question"], o) for o in q["options"]]
    return unique_argmax([-x for x in ov]) if max(ov) > 0 else None


def _convergence_scores(q):
    cw = [content_words(o) for o in q["options"]]
    return [sum(jaccard(cw[i], cw[j]) for j in range(4) if j != i) for i in range(4)]


def rule_convergence(q):
    s = _convergence_scores(q)
    return unique_argmax(s) if max(s) > 0 else None


def rule_divergence(q):
    s = _convergence_scores(q)
    return unique_argmax([-x for x in s]) if max(s) > 0 else None


def make_lexicon_pick(entries):
    """Pick the one option that matches the lexicon (abstain unless exactly one matches)."""
    def rule(q):
        hits = [i for i, o in enumerate(q["options"]) if matches_lexicon(o, entries)]
        return hits[0] if len(hits) == 1 else None
    return rule


def make_lexicon_odd_out(entries):
    """Three options match the lexicon, one does not: pick the one that does not."""
    def rule(q):
        miss = [i for i, o in enumerate(q["options"]) if not matches_lexicon(o, entries)]
        return miss[0] if len(miss) == 1 else None
    return rule


def make_scoped(rule, predicate):
    return lambda q: rule(q) if predicate(q) else None


def rule_ddr_state(q):
    if "DDR" not in q["question"] or "Bundesland" not in q["question"]:
        return None
    hits = [i for i, o in enumerate(q["options"]) if o.strip().lower() in EAST_STATES]
    return hits[0] if len(hits) == 1 else None


def rule_neighbor(q):
    if "Nachbarland" not in q["question"]:
        return None
    hits = [i for i, o in enumerate(q["options"]) if o.strip().lower() in NEIGHBORS]
    return hits[0] if len(hits) == 1 else None


def rule_age_18(q):
    hits = [i for i, o in enumerate(q["options"]) if re.fullmatch(r"18( Jahre)?\.?", o.strip())]
    return hits[0] if len(hits) == 1 else None


def make_key_numbers(key_numbers: set[float]):
    """Numeric question: the one option whose number is a 'key number' (see main: numbers that are the
    correct answer to at least two numeric questions)."""
    def rule(q):
        if not q["numeric"]:
            return None
        hits = [i for i, v in enumerate(q["num_values"]) if v in key_numbers]
        return hits[0] if len(hits) == 1 else None
    return rule


def picker_rules(key_numbers: set[float]) -> list[dict]:
    rules = [
        ("longest", "Longest option (characters)", "web", rule_longest),
        ("longest_words", "Longest option (words)", "web", rule_longest_words),
        ("shortest", "Shortest option", "own", rule_shortest),
        ("odd_length", "Option whose length is most unlike the others", "own", rule_odd_length),
        ("echo", "Option repeating the most words from the question", "own", rule_echo),
        ("anti_echo", "Option repeating the fewest words from the question", "own", rule_anti_echo),
        ("convergence", "Option sharing the most words with the other options (the 'centre' option)", "web",
         rule_convergence),
        ("divergence", "Option sharing the fewest words with the other options", "own", rule_divergence),
        ("num_lowest", "Numeric question: lowest number", "user", make_numeric_rank(0)),
        ("num_2nd_lowest", "Numeric question: second-lowest number", "own", make_numeric_rank(1)),
        ("num_2nd_highest", "Numeric question: second-highest number", "own", make_numeric_rank(2)),
        ("num_highest", "Numeric question: highest number", "own", make_numeric_rank(3)),
        ("longest_if_negated", "Question has nicht/kein: longest option", "own",
         make_scoped(rule_longest, lambda q: q["negated"])),
        ("shortest_if_negated", "Question has nicht/kein: shortest option", "own",
         make_scoped(rule_shortest, lambda q: q["negated"])),
        ("longest_if_not_negated", "Question without nicht/kein: longest option", "own",
         make_scoped(rule_longest, lambda q: not q["negated"])),
        ("ddr_state", "'Which state belonged to the DDR?': the one eastern state among the options", "knowledge",
         rule_ddr_state),
        ("neighbor", "'Which country is a neighbour?': the one actual neighbour among the options", "knowledge",
         rule_neighbor),
        ("age_18", "An option says 18: pick it", "mined", rule_age_18),
        ("key_numbers", "Numeric question: the one option that is a key number "
                        f"({', '.join(str(int(v)) for v in sorted(key_numbers))})", "mined",
         make_key_numbers(key_numbers)),
    ]
    for k in range(4):
        rules.append((f"pos_{'ABCD'[k]}", f"Always option {'ABCD'[k]}", "web", make_position(k)))
    for key, (label, entries) in LEXICONS.items():
        rules.append((f"lex_{key}", f"The only option with {label}", "own", make_lexicon_pick(entries)))
        rules.append((f"lex_{key}_odd_out", f"The only option WITHOUT {label}", "own", make_lexicon_odd_out(entries)))
    return [{"id": i, "name": n, "source": s, "fn": memo_by_qid(f)} for i, n, s, f in rules]


# ----------------------------------------------------------------------------- option features

@memo_by_qid
def option_features(q: dict) -> list[set[str]]:
    """Binary features per option; used for the 'cross it out' table and the naive-Bayes combination."""
    opts = q["options"]
    lens = [len(o) for o in opts]
    echo = [echo_overlap(q["question"], o) for o in opts]
    conv = _convergence_scores(q)
    feats = [set() for _ in range(4)]
    for i, o in enumerate(opts):
        f = feats[i]
        f.add(f"position_{'ABCD'[i]}")
        if lens[i] == max(lens) and lens.count(max(lens)) == 1:
            f.add("longest")
        if lens[i] == min(lens) and lens.count(min(lens)) == 1:
            f.add("shortest")
        if max(echo) > 0 and echo[i] == max(echo) and echo.count(max(echo)) == 1:
            f.add("most_echo")
        if max(echo) > 0 and echo[i] == 0:
            f.add("no_echo_while_others_echo")
        if max(conv) > 0 and conv[i] == max(conv) and conv.count(max(conv)) == 1:
            f.add("most_central")
        for key, (_, entries) in LEXICONS.items():
            if matches_lexicon(o, entries):
                f.add(f"lex_{key}")
        if "/" in o:
            f.add("gender_pair_slash")
        if re.search(r"\b(nicht|kein\w*)\b", o, re.I):
            f.add("option_negated")
        if q["numeric"] and len(set(q["num_values"])) == 4:
            rank = sorted(range(4), key=lambda j: q["num_values"][j]).index(i)
            f.add(["num_lowest", "num_2nd_lowest", "num_2nd_highest", "num_highest"][rank])
            if rank in (0, 3):
                f.add("num_extreme")
        if q["negated"]:
            f.add("in_negated_question")
    return feats


FEATURE_LABELS = {
    "longest": "is the longest option",
    "shortest": "is the shortest option",
    "most_echo": "repeats the most question words",
    "no_echo_while_others_echo": "repeats no question words (while another option does)",
    "most_central": "shares the most words with the other options",
    "gender_pair_slash": "contains a gender pair with '/' (Bürgerin/Bürger)",
    "option_negated": "contains nicht/kein",
    "num_lowest": "numeric question: lowest number",
    "num_2nd_lowest": "numeric question: second-lowest number",
    "num_2nd_highest": "numeric question: second-highest number",
    "num_highest": "numeric question: highest number",
    "num_extreme": "numeric question: lowest OR highest number",
    "in_negated_question": "any option of a nicht/kein question",
    **{f"position_{p}": f"is option {p}" for p in "ABCD"},
    **{f"lex_{k}": f"contains {v[0]}" for k, v in LEXICONS.items()},
}


# ----------------------------------------------------------------------------- statistics

def wilson(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def binom_tail_ge(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def binom_tail_le(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def evaluate_picker(rule: dict, qs: list[dict], n_tests: int) -> dict:
    fired = [(q, rule["fn"](q)) for q in qs]
    fired = [(q, i) for q, i in fired if i is not None]
    n = len(fired)
    hits = sum(1 for q, i in fired if i == q["answer_index"])
    res = {k: rule[k] for k in ("id", "name", "source")}
    res.update(support=n, coverage=n / len(qs), hits=hits, misses=n - hits, net_gain=2 * hits - n)
    if n:
        lo, hi = wilson(hits, n)
        p_better = binom_tail_ge(hits, n, BASELINE)
        p_worse = binom_tail_le(hits, n, BASELINE)
        cutoff = ALPHA / n_tests
        res.update(precision=hits / n, lift=hits / n / BASELINE, ci_low=lo, ci_high=hi,
                   p_better=p_better, p_worse=p_worse,
                   verdict="better" if p_better < cutoff else "worse" if p_worse < cutoff else "not significant")
    else:
        res.update(precision=None, lift=None, ci_low=None, ci_high=None, p_better=None, p_worse=None,
                   verdict="never fires")
    res["examples"] = [
        {"id": q["id"], "question": q["question"], "picked": q["options"][i], "answer": q["answer"],
         "hit": i == q["answer_index"]}
        for q, i in fired[:8]
    ]
    return res


def feature_table(qs: list[dict]) -> list[dict]:
    tot, corr, questions = Counter(), Counter(), Counter()
    for q in qs:
        seen = set()
        for i, feats in enumerate(option_features(q)):
            for f in feats:
                tot[f] += 1
                corr[f] += i == q["answer_index"]
                seen.add(f)
        questions.update(seen)
    rows = []
    for f in tot:
        n, c = tot[f], corr[f]
        lo, hi = wilson(c, n)
        rows.append({"feature": f, "label": FEATURE_LABELS.get(f, f), "options": n, "questions": questions[f],
                     "correct": c, "wrong": n - c, "p_correct": c / n, "lift": c / n / BASELINE,
                     "ci_low": lo, "ci_high": hi,
                     "p_more_often_correct": binom_tail_ge(c, n, BASELINE),
                     "p_more_often_wrong": binom_tail_le(c, n, BASELINE)})
    return sorted(rows, key=lambda r: (-r["p_correct"], r["feature"]))


# ----------------------------------------------------------------------------- learned models (with CV)

def folds(qs: list[dict]) -> list[list[dict]]:
    idx = list(range(len(qs)))
    random.Random(SEED).shuffle(idx)
    return [[qs[i] for i in idx[k::K_FOLDS]] for k in range(K_FOLDS)]


def fit_weights(train: list[dict], featurize) -> dict[str, float]:
    """Naive-Bayes style log-odds per feature, relative to the 1:3 prior odds of a random option."""
    tot, corr = Counter(), Counter()
    for q in train:
        for i, feats in enumerate(featurize(q)):
            for f in feats:
                tot[f] += 1
                corr[f] += i == q["answer_index"]
    return {f: math.log((corr[f] + 0.5) / (tot[f] - corr[f] + 0.5)) - math.log(1 / 3)
            for f in tot if tot[f] >= MIN_TOKEN_SUPPORT}


def predict(q: dict, weights: dict, featurize) -> int | None:
    scores = [sum(weights.get(f, 0.0) for f in feats) for feats in featurize(q)]
    return unique_argmax(scores)


@memo_by_qid
def token_features(q):
    return [{f"w:{w}" for w in words(o)} for o in q["options"]]


@memo_by_qid
def combined_features(q):
    return [a | b for a, b in zip(option_features(q), token_features(q))]


def accuracy(qs, picks) -> dict:
    fired = [(q, i) for q, i in zip(qs, picks) if i is not None]
    hits = sum(1 for q, i in fired if i == q["answer_index"])
    # abstentions count as a blind guess
    expected = hits + BASELINE * (len(qs) - len(fired))
    return {"n": len(qs), "fired": len(fired), "hits": hits, "accuracy_with_guessing": expected / len(qs)}


def cross_validate_model(qs, featurize) -> dict:
    per_fold, oof = [], {}
    for k, test in enumerate(folds(qs)):
        train = [q for q in qs if q not in test]
        w = fit_weights(train, featurize)
        train_acc = accuracy(train, [predict(q, w, featurize) for q in train])["accuracy_with_guessing"]
        picks = [predict(q, w, featurize) for q in test]
        test_acc = accuracy(test, picks)["accuracy_with_guessing"]
        per_fold.append({"fold": k, "train_accuracy": train_acc, "test_accuracy": test_acc})
        for q, i in zip(test, picks):
            oof[q["id"]] = i
    full_w = fit_weights(qs, featurize)
    in_sample = accuracy(qs, [predict(q, full_w, featurize) for q in qs])["accuracy_with_guessing"]
    return {"folds": per_fold,
            "train_accuracy": sum(f["train_accuracy"] for f in per_fold) / K_FOLDS,
            "test_accuracy": sum(f["test_accuracy"] for f in per_fold) / K_FOLDS,
            "in_sample_accuracy": in_sample,
            "oof_picks": oof, "weights": full_w}


# ----------------------------------------------------------------------------- decision list

def crossed_out(q: dict) -> set[int]:
    return {i for i, f in enumerate(option_features(q)) if f & set(CROSS_OUT)}


def fallback_pick(q: dict, preference: list[int]) -> int:
    """First position in the preference order that is not crossed out."""
    out = crossed_out(q)
    return next((k for k in preference if k not in out), preference[0])


def fit_decision_list(qs: list[dict], rules: list[dict], include_mined: bool = True) -> dict:
    """Greedy: repeatedly add the rule with the best precision on the still-uncovered questions
    (support >= MIN_SUPPORT, precision >= MIN_LIST_PRECISION). Uncovered questions fall back to the most
    common answer position among them, skipping crossed-out options. Mined rules are derived from the
    answers themselves, so the cross-validated fit leaves them out (include_mined=False)."""
    remaining = list(qs)
    steps = []
    candidates = [r for r in rules if not r["id"].startswith("pos_") and (include_mined or r["source"] != "mined")]
    while True:
        best = None
        for r in candidates:
            if any(s["id"] == r["id"] for s in steps):
                continue
            fired = [(q, r["fn"](q)) for q in remaining]
            fired = [(q, i) for q, i in fired if i is not None]
            if len(fired) < MIN_SUPPORT:
                continue
            hits = sum(1 for q, i in fired if i == q["answer_index"])
            prec = hits / len(fired)
            if prec >= MIN_LIST_PRECISION and (best is None or (prec, len(fired)) > (best[1], best[2])):
                best = (r, prec, len(fired), hits, {q["id"] for q, _ in fired})
        if best is None:
            break
        r, prec, n, hits, ids = best
        steps.append({"id": r["id"], "name": r["name"], "fired": n, "hits": hits, "precision": prec})
        remaining = [q for q in remaining if q["id"] not in ids]
    pos_hits = [sum(1 for q in remaining if q["answer_index"] == k) for k in range(4)]
    preference = sorted(range(4), key=lambda k: (-pos_hits[k], k))
    return {"steps": steps, "fallback_preference": preference, "fallback_n": len(remaining),
            "fallback_hits_plain": pos_hits[preference[0]],
            "fallback_hits_with_cross_out": sum(fallback_pick(q, preference) == q["answer_index"]
                                                for q in remaining)}


def apply_decision_list(dl: dict, q: dict, rules_by_id: dict) -> tuple[str, int]:
    for s in dl["steps"]:
        i = rules_by_id[s["id"]]["fn"](q)
        if i is not None:
            return s["id"], i
    pick = fallback_pick(q, dl["fallback_preference"])
    return f"fallback_{'ABCD'[pick]}", pick


def word_rules(qs: list[dict]) -> dict:
    """Single words as rules: 'an option with word w is (almost) always right / never right'. In-sample stats,
    plus how often the word qualifies on the training folds and how it then does on the held-out fold."""
    def stats(subset):
        tot, corr = Counter(), Counter()
        for q in subset:
            for i, o in enumerate(q["options"]):
                for w in set(words(o)):
                    tot[w] += 1
                    corr[w] += i == q["answer_index"]
        return tot, corr

    def direction(n, c):
        if n < MIN_WORD_SUPPORT:
            return None
        if c / n >= 0.6:
            return "positive"
        if c == 0 and n >= MIN_WORD_SUPPORT + 2:
            return "negative"
        return None

    tot, corr = stats(qs)
    rows = {w: {"word": w, "options": tot[w], "correct": corr[w], "p_correct": corr[w] / tot[w],
                "direction": direction(tot[w], corr[w]), "folds_qualified": 0, "heldout_options": 0,
                "heldout_correct": 0}
            for w in tot if direction(tot[w], corr[w])}
    for test in folds(qs):
        train = [q for q in qs if q not in test]
        t_tot, t_corr = stats(train)
        h_tot, h_corr = stats(test)
        for w, row in rows.items():
            if direction(t_tot[w], t_corr[w]) == row["direction"]:
                row["folds_qualified"] += 1
                row["heldout_options"] += h_tot[w]
                row["heldout_correct"] += h_corr[w]
    out = sorted(rows.values(), key=lambda r: (r["direction"], -r["p_correct"], -r["options"], r["word"]))
    return {"rules": out, "heldout_summary": _heldout_summary(out)}


def _heldout_summary(out: list[dict]) -> dict:
    agg = {}
    for d in ("positive", "negative"):
        sel = [r for r in out if r["direction"] == d]
        n = sum(r["heldout_options"] for r in sel)
        agg[d] = {"words": len(sel), "heldout_options": n,
                  "heldout_p_correct": sum(r["heldout_correct"] for r in sel) / n if n else None}
    return agg


CONDITIONAL_SELECTORS = ["longest", "shortest", "echo", "convergence", "divergence", "odd_length",
                         "pos_A", "pos_B", "pos_C", "pos_D", "lex_values", "lex_hedge", "lex_legal_remedy"]
MIN_TRIGGER_QUESTIONS = 5
MIN_CONDITIONAL_PRECISION = 0.6


def conditional_rules(qs: list[dict], rules_by_id: dict) -> dict:
    """'If the question contains word X, then <selector>' (e.g. 'Wann ... -> longest'). Every question word
    occurring in >= MIN_TRIGGER_QUESTIONS questions is crossed with every selector. Kept: precision >=
    MIN_CONDITIONAL_PRECISION on >= MIN_TRIGGER_QUESTIONS fired questions. The same mining is repeated on
    each training fold and the mined rules are scored on the held-out fold - the honest test of whether
    such rules are real or luck."""
    def by_trigger(subset):
        index = {}
        for q in subset:
            for w in set(words(q["question"])):
                index.setdefault(w, []).append(q)
        return index

    def mine(subset):
        index = by_trigger(subset)
        found = {}
        for w, w_qs in index.items():
            if len(w_qs) < MIN_TRIGGER_QUESTIONS:
                continue
            for sel in CONDITIONAL_SELECTORS:
                fn = rules_by_id[sel]["fn"]
                fired = [(q, fn(q)) for q in w_qs]
                fired = [(q, i) for q, i in fired if i is not None]
                if len(fired) < MIN_TRIGGER_QUESTIONS:
                    continue
                hits = sum(i == q["answer_index"] for q, i in fired)
                if hits / len(fired) >= MIN_CONDITIONAL_PRECISION:
                    found[(w, sel)] = (len(fired), hits)
        return found, sum(1 for v in index.values() if len(v) >= MIN_TRIGGER_QUESTIONS) * len(CONDITIONAL_SELECTORS)

    found, n_tests = mine(qs)
    heldout_fired = heldout_hits = 0
    stability = Counter()
    for test in folds(qs):
        test_ids = {q["id"] for q in test}
        f_train, _ = mine([q for q in qs if q["id"] not in test_ids])
        test_index = by_trigger(test)
        for (w, sel) in f_train:
            stability[(w, sel)] += 1
            fn = rules_by_id[sel]["fn"]
            for q in test_index.get(w, []):
                i = fn(q)
                if i is not None:
                    heldout_fired += 1
                    heldout_hits += i == q["answer_index"]
    rows = [{"trigger": w, "selector": sel, "fired": n, "hits": h, "precision": h / n,
             "p_better": binom_tail_ge(h, n, BASELINE), "folds_qualified": stability[(w, sel)]}
            for (w, sel), (n, h) in found.items()]
    rows.sort(key=lambda r: (-r["precision"], -r["fired"], r["trigger"], r["selector"]))
    return {"rules": rows, "n_tests": n_tests, "bonferroni_alpha": ALPHA / n_tests,
            "min_precision": MIN_CONDITIONAL_PRECISION, "min_questions": MIN_TRIGGER_QUESTIONS,
            "heldout_fired": heldout_fired, "heldout_hits": heldout_hits,
            "heldout_precision": heldout_hits / heldout_fired if heldout_fired else None}


# ----------------------------------------------------------------------------- exam model (exact)

def section_distribution(c: int, w: int, g: int, n: int, draw: int) -> dict[tuple[int, int], float]:
    """P(sure-correct, guessed) when `draw` questions are drawn without replacement from c sure-correct,
    w sure-wrong and g guessed questions."""
    total = math.comb(n, draw)
    dist = {}
    for i in range(min(c, draw) + 1):
        for j in range(min(w, draw - i) + 1):
            k = draw - i - j
            if k > g:
                continue
            p = math.comb(c, i) * math.comb(w, j) * math.comb(g, k) / total
            dist[(i, k)] = dist.get((i, k), 0.0) + p
    return dist


GUESS_TAIL = {(n, t): binom_tail_ge(max(t, 0), n, BASELINE) for n in range(34) for t in range(-33, 34)}


def exam_stats(outcome: dict[int, float], section: dict[int, str]) -> dict:
    """outcome per question id: 1 = answered right, 0 = answered wrong, 0.25 = blind guess."""
    dists, expected = [], 0.0
    for sec, (n, draw) in EXAM.items():
        vals = [outcome[i] for i in outcome if section[i] == sec]
        if len(vals) != n:
            raise ValueError(f"section {sec}: expected {n} questions, got {len(vals)}")
        c, w = vals.count(1), vals.count(0)
        g = n - c - w
        if g != sum(1 for v in vals if v == BASELINE):
            raise ValueError("outcomes must be 1, 0 or 0.25")
        dists.append(section_distribution(c, w, g, n, draw))
        expected += draw * (c + BASELINE * g) / n
    p_pass = 0.0
    for (i1, k1), p1 in dists[0].items():
        for (i2, k2), p2 in dists[1].items():
            p_pass += p1 * p2 * GUESS_TAIL[(k1 + k2, PASS_MARK - i1 - i2)]
    return {"expected_score": expected, "p_pass": p_pass}


def memorization_curve(outcome: dict[int, float], section: dict[int, str]) -> dict:
    """Memorize questions in the order that helps most: a Bayern question is drawn with p=3/10, a general
    one with 1/10, and memorizing gains (1 - current outcome)."""
    draw_p = {sec: d / n for sec, (n, d) in EXAM.items()}
    order = sorted(outcome, key=lambda i: (-draw_p[section[i]] * (1 - outcome[i]), i))
    current = dict(outcome)
    stats = [exam_stats(current, section)]
    for i in order:
        current[i] = 1
        stats.append(exam_stats(current, section))
    curve = [s["p_pass"] for s in stats]
    expected = [s["expected_score"] for s in stats]
    return {"p_pass_by_memorized": curve, "expected_score_by_memorized": expected,
            "memorize_for": {str(t): next(m for m, p in enumerate(curve) if p >= t) for t in PASS_TARGETS},
            # "minimal pass": on average you score exactly the pass mark
            "memorize_for_expected_pass_mark": next(m for m, e in enumerate(expected) if e >= PASS_MARK),
            "order": order}


# ----------------------------------------------------------------------------- main

def main() -> None:
    t0 = time.perf_counter()
    qs = [prepare(r) for r in json.loads(DATA.read_text(encoding="utf-8"))]
    if len(qs) != 310:
        raise ValueError(f"expected 310 questions, got {len(qs)}")
    section = {q["id"]: q["section"] for q in qs}
    numeric_answers = Counter(q["num_values"][q["answer_index"]] for q in qs if q["numeric"])
    key_numbers = {v for v, c in numeric_answers.items() if c >= 2}
    rules = picker_rules(key_numbers)
    rules_by_id = {r["id"]: r for r in rules}
    log.info(f"{len(qs)} questions, {len(rules)} picker rules")

    # answer position and numeric-rank distributions
    pos_counts = Counter("ABCD"[q["answer_index"]] for q in qs)
    numeric = [q for q in qs if q["numeric"] and len(set(q["num_values"])) == 4]
    num_rank = Counter(sorted(range(4), key=lambda i: q["num_values"][i]).index(q["answer_index"]) for q in numeric)
    stems = Counter(q["question"] for q in qs)
    repeated = [{"question": s, "count": n, "answers": [q["answer"] for q in qs if q["question"] == s]}
                for s, n in stems.items() if n > 1]

    pickers = [evaluate_picker(r, qs, len(rules)) for r in rules]
    pickers.sort(key=lambda r: (-(r["precision"] or 0), -r["support"]))
    features = feature_table(qs)
    words_mined = word_rules(qs)
    conditional = conditional_rules(qs, rules_by_id)
    log.info(f"conditional rules: {len(conditional['rules'])} kept of {conditional['n_tests']} tested, "
             f"held-out precision {conditional['heldout_precision']}")

    hand_cv = cross_validate_model(qs, option_features)
    token_cv = cross_validate_model(qs, token_features)
    combined_cv = cross_validate_model(qs, combined_features)
    log.info(f"CV accuracy (test folds): hand features {hand_cv['test_accuracy']:.3f}, "
             f"words {token_cv['test_accuracy']:.3f}, both {combined_cv['test_accuracy']:.3f}")

    dl = fit_decision_list(qs, rules)
    dl_rows = []
    for q in qs:
        rid, i = apply_decision_list(dl, q, rules_by_id)
        dl_rows.append({"id": q["id"], "section": q["section"], "question": q["question"], "rule": rid,
                        "picked_index": i, "picked": q["options"][i], "answer": q["answer"],
                        "hit": i == q["answer_index"]})
    dl["accuracy"] = sum(r["hit"] for r in dl_rows) / len(qs)
    dl["questions"] = dl_rows

    # decision list fitted on 4/5 of the questions, applied to the held-out 1/5
    dl_oof = {}
    dl_cv_folds = []
    for k, test in enumerate(folds(qs)):
        train = [q for q in qs if q not in test]
        dlk = fit_decision_list(train, rules, include_mined=False)
        picks = {q["id"]: apply_decision_list(dlk, q, rules_by_id)[1] for q in test}
        dl_oof.update(picks)
        dl_cv_folds.append({"fold": k, "rules": [s["id"] for s in dlk["steps"]],
                            "test_accuracy": sum(picks[q["id"]] == q["answer_index"] for q in test) / len(test)})
    dl["cv_folds"] = dl_cv_folds
    dl["cv_accuracy"] = sum(dl_oof[q["id"]] == q["answer_index"] for q in qs) / len(qs)
    log.info(f"decision list: {len(dl['steps'])} rules, in-sample {dl['accuracy']:.3f}, CV {dl['cv_accuracy']:.3f}")

    def outcome_from_picks(picks: dict) -> dict:
        return {q["id"]: BASELINE if picks.get(q["id"]) is None else float(picks[q["id"]] == q["answer_index"])
                for q in qs}

    blind = {q["id"]: BASELINE for q in qs}
    strategies = {
        "blind guessing": blind,
        "always B": outcome_from_picks({q["id"]: 1 for q in qs}),
        "longest option (else guess)": outcome_from_picks({q["id"]: rule_longest(q) for q in qs}),
        "decision list (in-sample)": outcome_from_picks({r["id"]: r["picked_index"] for r in dl_rows}),
        "decision list (cross-validated)": outcome_from_picks(dl_oof),
        "naive Bayes, hand features (cross-validated)": outcome_from_picks(hand_cv["oof_picks"]),
        "naive Bayes, words + features (cross-validated)": outcome_from_picks(combined_cv["oof_picks"]),
    }
    # If the printed sheets shuffled the options, the position fallback (B, D, A, C) loses its edge, while the
    # content rules (key numbers, DDR states, values words, ...) do not care about order. Conservative: the
    # fallback becomes a blind guess (crossing out options would help a little, see shuffled_fallback below).
    strategies["decision list, options shuffled"] = {
        r["id"]: BASELINE if r["rule"].startswith("fallback_") else float(r["hit"]) for r in dl_rows}
    fb = [q for q, r in zip(qs, dl_rows) if r["rule"].startswith("fallback_")]
    guess_after_cross_out = [0.0 if q["answer_index"] in crossed_out(q) else 1 / (4 - len(crossed_out(q))) for q in fb]
    shuffled_fallback = {"questions": len(fb),
                         "mean_p_blind_guess": BASELINE,
                         "mean_p_guess_after_cross_out": sum(guess_after_cross_out) / len(fb),
                         "questions_with_cross_out": sum(1 for q in fb if crossed_out(q)),
                         "answer_crossed_out": sum(1 for q in fb if q["answer_index"] in crossed_out(q))}
    exam = {name: exam_stats(o, section) for name, o in strategies.items()}
    for name, s in exam.items():
        log.info(f"exam: {name:48s} expected {s['expected_score']:.1f}/33, P(pass) {s['p_pass']:.4f}")
    curves = {name: memorization_curve(strategies[name], section)
              for name in ("blind guessing", "always B", "decision list (in-sample)", "decision list, options shuffled")}
    for name, c in curves.items():
        levels = ", ".join(f"{float(t):.0%}: {m}" for t, m in c["memorize_for"].items())
        log.info(f"memorize ({name}): expected {PASS_MARK}/33 at {c['memorize_for_expected_pass_mark']}; "
                 f"P(pass) {levels}")

    for model in (hand_cv, token_cv, combined_cv):
        model.pop("oof_picks")
    token_cv["top_words"] = sorted(
        ({"word": f[2:], "weight": w} for f, w in token_cv.pop("weights").items()), key=lambda r: (-r["weight"], r["word"]))
    hand_cv["weights"] = dict(sorted(hand_cv["weights"].items(), key=lambda kv: (-kv[1], kv[0])))
    combined_cv.pop("weights")

    result = {
        "meta": {"generated": time.strftime("%Y-%m-%d %H:%M"), "n_questions": len(qs), "seed": SEED,
                 "baseline": BASELINE, "k_folds": K_FOLDS, "n_picker_rules": len(rules),
                 "bonferroni_alpha": ALPHA / len(rules), "min_support": MIN_SUPPORT,
                 "min_list_precision": MIN_LIST_PRECISION, "pass_mark": PASS_MARK, "exam": EXAM,
                 "pass_targets": PASS_TARGETS,
                 "cross_out": CROSS_OUT, "key_numbers": sorted(key_numbers),
                 "min_word_support": MIN_WORD_SUPPORT},
        "position_counts": {p: pos_counts[p] for p in "ABCD"},
        "position_p_values": {p: {"more": binom_tail_ge(pos_counts[p], len(qs), BASELINE),
                                  "fewer": binom_tail_le(pos_counts[p], len(qs), BASELINE)} for p in "ABCD"},
        "numeric": {"n": len(numeric), "rank_counts": [num_rank[k] for k in range(4)],
                    "ids": [q["id"] for q in numeric]},
        "repeated_stems": repeated,
        "picker_rules": pickers,
        "option_features": features,
        "word_rules": words_mined,
        "conditional_rules": conditional,
        "cv": {"hand_features": hand_cv, "words": token_cv, "words_and_features": combined_cv},
        "decision_list": dl,
        "exam": exam,
        "shuffled_fallback": shuffled_fallback,
        "memorization": curves,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info(f"wrote {OUT.relative_to(ROOT)} in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
