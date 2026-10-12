# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pillow==12.3.0",
# ]
# ///
"""Check the video scripts (videos/scripts/*.md) before voicing or rendering, without any API call.

Per script: every scene has Voice RU, Voice EN, On screen, Visual and Questions; the {Q} markers of both languages
match the Questions line; the cards cover exactly the questions of the script's lessons; no memorize question is left
to the recap (last scene); no dashes or curly quotes (the voice reads them oddly); every subtitle fits the 3-line box
and every big term card fits the screen (with the renderer's own chunks() and wrap()). Logs the estimated
duration per language from the speaking rates measured for Charon. --write puts those estimates into the scene
headings ("(~29 s)") and the "Lessons:" line.

Run:      uv run videos/pipeline/non_essential/check_scripts.py [--write]
Runtime:  ~10 s (measured 8 s)
"""

import json
import logging
import re
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render  # noqa: E402  (the renderer's chunks, wrap, fonts and limits)

REPO = render.REPO
WPM = {"RU": 103, "EN": 131}   # measured 2026-10-06: Charon, calm style
CARD_S = 3                     # minimum seconds a card (or a grid of cards said together) stays up
BAD_CHARS = r"[–—“”„‘’«»]"

log = logging.getLogger("check_scripts")


def main() -> None:
    (REPO / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(REPO / "logs" / "check_scripts.log", encoding="utf-8")])
    t0 = time.time()
    write = "--write" in sys.argv
    lessons = {l["topic"]: l for l in json.loads((REPO / "data" / "lessons.json").read_text(encoding="utf-8"))["lessons"]}
    topics = {t["key"]: t for t in json.loads((REPO / "data" / "topics.json").read_text(encoding="utf-8"))["topics"]}
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    failed, shortest = [], (999, "")
    for path in sorted(render.SCRIPTS.glob("*.md")):
        s = path.read_text(encoding="utf-8")
        keys = re.findall(r"`(\w+)`", re.search(r"Lessons?: ((?:`\w+`(?:, )?)+)", s).group(1))
        sense = set().union(*(lessons[k]["common_sense"] for k in keys))
        allq = set().union(*(topics[k]["questions"] for k in keys))
        problems = [f"bad characters {set(c)}" for c in [re.findall(BAD_CHARS, s)] if c]
        parts = re.split(r"(\n## )", s)
        out, total, seen = [parts[0]], {"RU": 0, "EN": 0}, {"RU": [], "EN": []}
        nscenes = (len(parts) - 1) // 2
        for k in range(nscenes):
            sc = parts[2 * k + 2]
            f = {m.group(1): m.group(2).strip() for m in re.finditer(r"- \*\*(Voice RU|Voice EN|On screen|Visual|Questions):\*\* (.*)", sc)}
            if len(f) != 5:
                problems.append(f"scene {k + 1}: fields {sorted(f)}")
                continue
            listed = [] if f["Questions"] == "-" else [int(x) for x in f["Questions"].split(",")]
            sec = 0
            for lang in ("RU", "EN"):
                v = f[f"Voice {lang}"]
                marks = [int(x) for x in re.findall(r"\{Q(\d+)\}", v)]
                if sorted(marks) != sorted(listed):
                    problems.append(f"scene {k + 1} {lang}: markers {marks} vs Questions {listed}")
                seen[lang] += marks
                text = re.sub(r"\s*\{Q\d+\}\s*", " ", v).strip()
                for c in render.chunks(text):
                    n = len(render.wrap(draw, c, render.font(28), render.W - 220))
                    if n > render.SUB_LINES:
                        problems.append(f"scene {k + 1} {lang}: subtitle needs {n} lines: {c[:60]}")
                    shortest = min(shortest, (len(c), f"{path.stem} {lang} scene {k + 1}: {c}"))
                groups = len(re.findall(r"(?:\{Q\d+\}\s*)+", v))
                t = max(round(len(text.split()) / WPM[lang] * 60), CARD_S * groups, 5)
                total[lang] += t
                sec = max(sec, t)
            if not f["Visual"].startswith("exam:"):   # shown big until the first card (the whole scene if it has none)
                fits = any(len(render.wrap(draw, f["On screen"], render.font(size, True), render.W - 260)) <= n for size, n in ((44, 3), (36, 5), (30, 7)))
                if not fits:
                    problems.append(f"scene {k + 1}: term card does not fit even at 30 px")
            if k == nscenes - 1 and set(listed) - sense:
                problems.append(f"memorize questions {sorted(set(listed) - sense)} only in the recap")
            out += [parts[2 * k + 1], re.sub(r"\(~\d+ s\)", f"(~{sec} s)", sc, count=1)]
        for lang in ("RU", "EN"):
            if sorted(seen[lang]) != sorted(allq):
                problems.append(f"{lang}: cards {sorted(seen[lang])} != lessons' questions {sorted(allq)}")
        mmss = lambda x: f"{x // 60}:{x % 60:02d}"
        if write:
            s2 = re.sub(r"(Lessons?: (?:`\w+`(?:, )?)+ · )(~RU [\d:]+ / EN [\d:]+ · )?",
                        lambda m: m.group(1) + f"~RU {mmss(total['RU'])} / EN {mmss(total['EN'])} · ", "".join(out), count=1)
            path.write_text(s2, encoding="utf-8")
        log.info(f"{path.stem:28s} RU ~{mmss(total['RU'])}  EN ~{mmss(total['EN'])}  {'OK' if not problems else problems}")
        if problems:
            failed.append(path.stem)
    log.info(f"shortest subtitle: {shortest[0]} characters ({shortest[1]})")
    if failed:
        log.error(f"problems in {failed}")
        raise SystemExit(1)
    log.info(f"all scripts OK in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
