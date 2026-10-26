"""Check whether printed exam sheets list the answer options in catalog order.

Matches every question on the official BAMF sample sheets (official/musterbogen_einbuergerungstest*.pdf) to the
current catalog (official/gesamtfragenkatalog-*.pdf, all 460 questions incl. all 16 states) by its set of options,
then checks whether the four options appear in the same order. If BAMF shuffled options per sheet, a question would
keep catalog order with probability 1/24.

Run:      python scripts/check_sheet_order.py
Output:   results/sheet_order_check.json
Runtime:  ~30 s (measured on this laptop; the fuzzy match against all 460 catalog questions dominates)
"""

import difflib
import json
import logging
import math
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_dataset import parse_catalog, pdf_text  # noqa: E402

SHEETS = sorted((ROOT / "official").glob("musterbogen_einbuergerungstest*.pdf"))
OUT = ROOT / "results" / "sheet_order_check.json"
MIN_FUZZY_SCORE = 0.8   # mean best-match similarity of the 4 options for a fuzzy question match

(ROOT / "logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler(ROOT / "logs" / "check_sheet_order.log", encoding="utf-8")],
)
log = logging.getLogger("check_sheet_order")


def norm(option: str) -> str:
    """Order-insensitive word bag, so 'Erster Minister/ Erste Ministerin' == 'Erste Ministerin/Erster Minister'."""
    s = re.sub(r"^bild (\d)$", r"\1", option.strip().lower())
    return " ".join(sorted(re.findall(r"\w+", s)))


def parse_sheet(path: Path) -> dict:
    text = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
                          capture_output=True, check=True).stdout.decode("utf-8")
    header = {key: (m.group(1).strip() if (m := re.search(pat, text)) else None)
              for key, pat in [("pruefungsnr", r"Prüfungsnr\.:\s*(\d+)"),
                               ("testfragebogennr", r"Testfragebogennr\.:\s*(\d+)"),
                               ("bundesland", r"Bundesland:\s*([^\n]+)")]}
    questions, cur, indent = [], None, None
    for line in text.replace("\f", "\n").split("\n"):
        s = line.strip()
        if not s or (s.startswith("Einbürgerungstest") and "Prüfungsnr" in s):
            continue
        m = re.match(r"^Frage (\d+)", s)
        if m:
            cur = {"number": int(m.group(1)), "options": []}
            questions.append(cur)
            continue
        if cur is None:
            continue
        if s.startswith("¨"):
            cur["options"].append(s.lstrip("¨").strip())
            indent = len(line) - len(line.lstrip())
        elif cur["options"] and len(line) - len(line.lstrip()) > indent:
            cur["options"][-1] += " " + s
    bad = [q["number"] for q in questions if len(q["options"]) != 4]
    if len(questions) != 33 or bad:
        raise ValueError(f"{path.name}: parsed {len(questions)} questions, wrong option count in {bad}")
    return {"file": path.name, **header, "questions": questions}


def catalog_entries() -> list[dict]:
    entries = []
    for section, questions in parse_catalog(pdf_text()).items():
        for num, q in questions.items():
            entries.append({"section": section, "number": num, "question": q["question"], "options": q["options"],
                            "norm": [norm(o) for o in q["options"]]})
    bayern = json.loads((ROOT / "data" / "questions_bayern.json").read_text(encoding="utf-8"))
    for r in bayern:  # OET wording (male-first gender pairs) as an alternative spelling of the same question
        entries.append({"section": r["section"], "number": r["catalog_number"], "question": r["question"],
                        "options": r["options_oet"], "norm": [norm(o) for o in r["options_oet"]], "oet": True})
    return entries


def match(sheet_q: dict, catalog: list[dict]) -> dict:
    sn = [norm(o) for o in sheet_q["options"]]
    exact = [c for c in catalog if sorted(c["norm"]) == sorted(sn)]
    keys = {(c["section"], c["number"]) for c in exact}
    if len(keys) > 1:
        return {"status": "ambiguous", "candidates": sorted(f"{s} {n}" for s, n in keys)}
    if exact:
        c = exact[0]
        mapping = [c["norm"].index(x) for x in sn]
        return {"status": "exact", "section": c["section"], "number": c["number"], "question": c["question"],
                "mapping": mapping, "score": 1.0}
    best = None
    for c in catalog:
        sims = [[difflib.SequenceMatcher(None, a, b).ratio() for b in c["norm"]] for a in sn]
        score = sum(max(row) for row in sims) / 4
        if best is None or score > best[0]:
            best = (score, c, [max(range(4), key=lambda j: row[j]) for row in sims])
    score, c, mapping = best
    if score < MIN_FUZZY_SCORE or len(set(mapping)) != 4:
        return {"status": "unmatched", "best_score": round(score, 3),
                "best_guess": f"{c['section']} {c['number']}: {c['question'][:80]}"}
    return {"status": "fuzzy", "section": c["section"], "number": c["number"], "question": c["question"],
            "mapping": mapping, "score": round(score, 3)}


def main() -> None:
    t0 = time.perf_counter()
    if len(SHEETS) < 1:
        raise FileNotFoundError("no official/musterbogen_einbuergerungstest*.pdf found")
    catalog = catalog_entries()
    log.info(f"catalog: {len({(c['section'], c['number']) for c in catalog})} questions; sheets: "
             f"{[p.name for p in SHEETS]}")
    report = {"generated": time.strftime("%Y-%m-%d %H:%M"), "sheets": []}
    total_matched = total_same = 0
    for path in SHEETS:
        sheet = parse_sheet(path)
        rows = []
        for q in sheet["questions"]:
            m = match(q, catalog)
            if "mapping" in m:
                m["same_order"] = m["mapping"] == [0, 1, 2, 3]
            rows.append({"sheet_number": q["number"], "sheet_options": q["options"], **m})
        matched = [r for r in rows if "mapping" in r]
        # questions whose options are only picture labels say nothing about shuffling
        informative = [r for r in matched if sorted(norm(o) for o in r["sheet_options"]) != ["1", "2", "3", "4"]]
        same = sum(r["same_order"] for r in informative)
        total_matched += len(informative)
        total_same += same
        summary = {"file": sheet["file"], "pruefungsnr": sheet["pruefungsnr"],
                   "testfragebogennr": sheet["testfragebogennr"], "bundesland": sheet["bundesland"],
                   "questions": len(rows), "exact": sum(r["status"] == "exact" for r in rows),
                   "fuzzy": sum(r["status"] == "fuzzy" for r in rows),
                   "ambiguous": sum(r["status"] == "ambiguous" for r in rows),
                   "unmatched": sum(r["status"] == "unmatched" for r in rows),
                   "informative_matched": len(informative), "same_order": same,
                   "different_order": len(informative) - same}
        log.info(f"{path.name}: {summary}")
        report["sheets"].append({**summary, "rows": rows})
    # chance of seeing this if options were shuffled uniformly per question
    report["total_informative_matched"] = total_matched
    report["total_same_order"] = total_same
    report["log10_p_all_same_if_shuffled"] = total_same * math.log10(1 / 24)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info(f"total: {total_same}/{total_matched} matched questions in catalog order; if shuffled, chance of that "
             f"= 10^{report['log10_p_all_same_if_shuffled']:.0f}. Wrote {OUT.relative_to(ROOT)} in "
             f"{time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
