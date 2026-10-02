"""Build the Bayern question dataset (310 questions with answers) from the two official BAMF sources.

Sources (both already in the repo, nothing is downloaded here):
  - official/gesamtfragenkatalog-lebenindeutschland_2025-05-26.pdf
      BAMF PDF catalog (Stand 07.05.2025). Has the question text, but does NOT mark the correct answer.
  - data/raw/oet_*.json
      Scrape of the BAMF Online-Testcenter (oet.bamf.de, Bundesland = Bayern), made with
      scripts/oet_scrape.js. Has the options and the correct answer, but the question stem is an image.

The question text comes from the PDF, options and correct answer from the Online-Testcenter.
Both option lists are kept and matched against each other; a poor match aborts the build.

Outputs:
  data/questions_bayern.json, data/questions_bayern.csv, data/images/NNN.png (picture questions),
  QUESTIONS_AND_ANSWERS_BAYERN.md

Requires: Python 3.10+ (stdlib only) and `pdftotext` (poppler) on PATH.
Run:      python scripts/build_dataset.py
Runtime:  ~4-12 s (measured on this laptop; mostly pdftotext on the 9 MB PDF).
"""

import base64
import csv
import difflib
import json
import logging
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "official" / "gesamtfragenkatalog-lebenindeutschland_2025-05-26.pdf"
RAW_FILES = sorted((ROOT / "data" / "raw").glob("oet_*.json"))
OUT_JSON = ROOT / "data" / "questions_bayern.json"
OUT_CSV = ROOT / "data" / "questions_bayern.csv"
OUT_MD = ROOT / "QUESTIONS_AND_ANSWERS_BAYERN.md"
IMG_DIR = ROOT / "data" / "images"
STATE = "Bayern"

# Picture questions have a stem image of tens of KB; text-only stems are ~1-2 KB.
PICTURE_STEM_MIN_BYTES = 6000
# Below this similarity a PDF option and its OET counterpart are treated as different answers.
MIN_OPTION_SIMILARITY = 0.6

OPTION_MARK = re.compile(r"^\s*[□]\s*")
FOOTER = re.compile(r"\s*Seite \d+ von \d+\s*$")
CAPTION = re.compile(r"^(Bild \d\s*)+$")

log = logging.getLogger("build_dataset")


def setup_logging() -> None:
    """Called from main() so other scripts can import the parser without writing to this script's log."""
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(ROOT / "logs" / "build_dataset.log", encoding="utf-8"),
        ],
    )


def pdf_text() -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(PDF), "-"],
        capture_output=True, check=True,
    )
    return result.stdout.decode("utf-8")


def parse_catalog(text: str) -> dict[str, dict[int, dict]]:
    """Return {section: {catalog_number: {"question", "options"}}}; section is "general" or a state name."""
    sections: dict[str, dict[int, dict]] = {"general": {}}
    section = "general"
    current = None
    current_num = None
    last_option_indent = None

    for raw_line in text.replace("\f", "\n").split("\n"):
        line = FOOTER.sub("", raw_line).rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if re.match(r"^Teil I+$", stripped):
            continue  # part header; it is indented, so it would otherwise be glued to the previous option

        state = re.match(r"^Fragen für das Bundesland (.+)$", stripped)
        if state:
            section = state.group(1).strip()
            sections[section] = {}
            current = None
            continue

        task = re.match(r"^Aufgabe (\d+)$", stripped)
        if task:
            num = int(task.group(1))
            if num in sections[section]:
                raise ValueError(f"duplicate Aufgabe {num} in section {section}")
            current = {"question": [], "options": []}
            sections[section][num] = current
            current_num = num
            last_option_indent = None
            continue

        if current is None:
            continue  # title page, Teil I/II headers, notes

        if OPTION_MARK.match(line):
            current["options"].append([OPTION_MARK.sub("", line).strip()])
            last_option_indent = len(line) - len(line.lstrip())
        elif current["options"]:
            # Wrapped option text is indented deeper than the option marker.
            indent = len(line) - len(line.lstrip())
            if last_option_indent is None or indent <= last_option_indent:
                raise ValueError(f"{section} Aufgabe {current_num}: unexpected text after options: {stripped!r}")
            current["options"][-1].append(stripped)
        elif not CAPTION.match(stripped):
            current["question"].append(stripped)

    for name, questions in sections.items():
        for num, q in questions.items():
            q["question"] = " ".join(q["question"])
            q["options"] = [" ".join(parts) for parts in q["options"]]
            if len(q["options"]) != 4 or not q["question"]:
                raise ValueError(f"{name} Aufgabe {num}: {len(q['options'])} options, question={q['question']!r}")
    return sections


def load_oet() -> list[dict]:
    questions = []
    for path in RAW_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, str):  # browser_evaluate wraps the JSON string in another JSON string
            data = json.loads(data)
        if not isinstance(data, list):
            raise TypeError(f"{path.name}: expected a list, got {type(data).__name__}")
        questions.extend(data)
    nums = [q["num"] for q in questions]
    if nums != list(range(1, 311)):
        raise ValueError(f"OET scrape is not questions 1..310 in order (got {len(nums)} entries)")
    return questions


def norm(s: str) -> str:
    """Normalize the cosmetic differences between the PDF and OET wording.

    The OET site writes picture options as "1" (PDF: "Bild 1") and gender pairs male-first
    ("verteidigt den Angeklagten / die Angeklagte"); the 2025 PDF puts the female form first, also
    mid-sentence. Comparing the sorted words makes the pair order irrelevant.
    """
    s = re.sub(r"^bild (\d)$", r"\1", s.strip().lower())
    return " ".join(sorted(re.findall(r"\w+", s)))


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def main() -> None:
    setup_logging()
    t0 = time.perf_counter()
    if not RAW_FILES:
        raise FileNotFoundError("no data/raw/oet_*.json files - run scripts/oet_scrape.js first")

    catalog = parse_catalog(pdf_text())
    log.info(f"PDF: {len(catalog['general'])} general questions, {len(catalog) - 1} state sections")
    if len(catalog["general"]) != 300 or len(catalog.get(STATE, {})) != 10:
        raise ValueError(f"expected 300 general + 10 {STATE} questions in the PDF")
    oet = load_oet()

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    low_similarity = []
    missing_stem = []
    for q in oet:
        num = q["num"]
        section, catalog_number = ("general", num) if num <= 300 else (STATE, num - 300)
        pdf_q = catalog[section][catalog_number]

        correct = [i for i, o in enumerate(q["opts"]) if o["correct"]]
        if len(q["opts"]) != 4 or len(correct) != 1:
            raise ValueError(f"question {num}: OET scrape has {len(q['opts'])} options, {len(correct)} marked correct")
        answer_index = correct[0]

        oet_options = [o["text"] for o in q["opts"]]
        sims = [similarity(a, b) for a, b in zip(oet_options, pdf_q["options"])]
        if min(sims) < MIN_OPTION_SIMILARITY:
            low_similarity.append((num, oet_options, pdf_q["options"], sims))

        # The OET site shows no stem at all for a handful of questions (only an internal ID such as
        # "ET2021a_Meinungsfreiheit"); the PDF text covers those. A picture question must have its image.
        image = None
        is_picture = pdf_q["options"] == ["Bild 1", "Bild 2", "Bild 3", "Bild 4"]
        if q["stem_img"] is None:
            if is_picture:
                raise ValueError(f"picture question {num} has no image in the OET scrape")
            missing_stem.append(num)
        else:
            stem_bytes = base64.b64decode(q["stem_img"].split(",", 1)[1])
            if len(stem_bytes) >= PICTURE_STEM_MIN_BYTES:
                image = f"data/images/{num:03d}.png"
                (ROOT / image).write_bytes(stem_bytes)

        # Option order is identical in both sources (checked by the similarity test below), so the
        # OET answer index applies to the PDF wording, which is newer and matches the question text.
        records.append({
            "id": num,
            "section": section,
            "catalog_number": catalog_number,
            "question": pdf_q["question"],
            "options": pdf_q["options"],
            "options_oet": oet_options,
            "answer_index": answer_index,
            "answer": pdf_q["options"][answer_index],
            "image": image,
        })

    if low_similarity:
        for num, a, b, sims in low_similarity:
            log.error(f"question {num}: OET options {a} do not match PDF options {b} (similarity {sims})")
        raise ValueError(f"{len(low_similarity)} questions have mismatched options between PDF and OET")
    log.info(f"OET shows no question stem for {len(missing_stem)} questions (text taken from PDF): {missing_stem}")

    OUT_JSON.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "section", "catalog_number", "question", "option_a", "option_b", "option_c",
                    "option_d", "answer_letter", "answer", "image"])
        for r in records:
            w.writerow([r["id"], r["section"], r["catalog_number"], r["question"], *r["options"],
                        "ABCD"[r["answer_index"]], r["answer"], r["image"] or ""])
    OUT_MD.write_text(render_markdown(records), encoding="utf-8")

    n_img = sum(1 for r in records if r["image"])
    log.info(f"wrote {len(records)} questions ({n_img} with images) to {OUT_JSON.name}, {OUT_CSV.name}, {OUT_MD.name}")
    log.info(f"done in {time.perf_counter() - t0:.1f} s")


def render_markdown(records: list[dict]) -> str:
    out = [
        "# Einbürgerungstest - all 310 questions with answers (Bayern)",
        "",
        "300 general questions + 10 Bayern questions. The real test draws 30 general + 3 Bayern "
        "questions; 17 correct out of 33 is a pass.",
        "",
        "- Question text: official BAMF catalog PDF, Stand 07.05.2025 (`official/`).",
        "- Options and correct answer: official BAMF Online-Testcenter (oet.bamf.de), scraped 2026-10-02.",
        "- The correct answer is **bold** and marked with ✅. Picture questions show the official image.",
        "",
        "Generated by `scripts/build_dataset.py` - do not edit by hand.",
        "",
        "## Teil I - Allgemeine Fragen (1-300)",
        "",
    ]
    for r in records:
        if r["id"] == 301:
            out += ["## Teil II - Fragen für das Bundesland Bayern (301-310)", ""]
        label = f"{r['id']}" if r["section"] == "general" else f"{r['id']} (Bayern {r['catalog_number']})"
        out.append(f"### {label}. {r['question']}")
        out.append("")
        if r["image"]:
            out += [f"![Frage {r['id']}]({r['image']})", ""]
        for i, opt in enumerate(r["options"]):
            letter = "ABCD"[i]
            out.append(f"- ✅ **{letter}) {opt}**" if i == r["answer_index"] else f"- {letter}) {opt}")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    main()
