"""Local page to watch all rendered videos side by side: videos/build/index.html (ignored), one collapsible section per
video with Russian and English next to each other, table of contents on top. The page plays the files in videos/mp4/
from disk, so it is for this machine only, not for sending (the videos are 111 MB).

Run:      uv run --no-project python videos/pipeline/non_essential/listen_page.py   (then open videos/build/index.html)
Runtime:  <1 s
"""

import html
import logging
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MP4 = REPO / "videos" / "mp4"
OUT = REPO / "videos" / "build" / "index.html"

log = logging.getLogger("listen_page")


def main() -> None:
    (REPO / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(REPO / "logs" / "listen_page.log", encoding="utf-8")])
    scripts = sorted((REPO / "videos" / "scripts").glob("*.md"))
    toc, sections = [], []
    for p in scripts:
        title = re.search(r"^# (.+)$", p.read_text(encoding="utf-8"), re.M).group(1)
        cells = []
        for lang, label in (("ru", "Русский"), ("en", "English")):
            f = MP4 / f"{p.stem}.{lang}.mp4"
            if not f.exists():
                raise SystemExit(f"missing {f.relative_to(REPO)}: render it first (videos/pipeline/render.py)")
            cells.append(f'<figure><figcaption>{label} · {f.stat().st_size / 1e6:.1f} MB</figcaption>'
                         f'<video controls preload="metadata" src="../mp4/{f.name}"></video></figure>')
        toc.append(f'<a href="#{p.stem}">{html.escape(title)}</a>')
        sections.append(f'<details open id="{p.stem}"><summary>{html.escape(title)}</summary><div class="pair">{"".join(cells)}</div></details>')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Explainer videos</title><style>
body{{font-family:system-ui,'Segoe UI',sans-serif;margin:0 auto;padding:16px;max-width:1200px;background:#f6f7f9;color:#1b1f24}}
nav{{display:flex;flex-wrap:wrap;gap:6px 16px;margin-bottom:16px}}
details{{background:#fff;border:1px solid #d9dee5;border-radius:10px;padding:12px 16px;margin-bottom:14px}}
summary{{font-weight:700;font-size:1.1rem;cursor:pointer}}
.pair{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;margin-top:10px}}
figure{{margin:0}} figcaption{{color:#5d6673;font-size:.9rem;margin-bottom:6px}} video{{width:100%;border-radius:8px;background:#000}}
</style></head><body>
<h1>Explainer videos</h1>
<nav>{"".join(toc)}</nav>
{"".join(sections)}
</body></html>""", encoding="utf-8")
    log.info(f"wrote {OUT.relative_to(REPO)} with {len(scripts)} videos")


if __name__ == "__main__":
    main()
