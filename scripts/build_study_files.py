"""Build the readable study files: one per topic and language, as standalone HTML and as PDF.

study/<lang>/<NN>_<topic>.html and .pdf (NN = position in data/topics.json, lang = en | ru), plus study/index.html
listing them all. Each file holds the topic's lesson (60-second summary, facts, traps) and every exam question of the
topic with its correct answer, the translation (English or Russian) and the picture, so it can be read offline or
printed. The HTML embeds everything (CSS, pictures as data URIs); the PDF is printed from it by headless Chrome.

study/manifest.json records a SHA-256 of every input (text inputs with CRLF read as LF, so Windows and the Linux
deploy agree). The site build (app/vite.config.ts) refuses to publish the files if an input changed since they
were built, so a lesson edit can never ship next to an old PDF.

Needs: Python 3.10+ (stdlib only), Google Chrome (for the PDFs; path in CHROME).
Run:      python scripts/build_study_files.py
Runtime:  ~2.5-5 min (measured 145 s and 289 s on this laptop; nearly all of it is Chrome printing 48 PDFs)
"""

import base64
import hashlib
import html
import json
import logging
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "study"
CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
SITE = "https://hayktarkhanyan.github.io/germany-naturalization-test/"
LANGS = ("en", "ru")
TEXT_INPUTS = ["data/topics.json", "data/lessons.json", "data/lessons_ru.json", "data/questions_bayern.json",
               "data/translations_en.json", "data/translations_ru.json", "scripts/build_study_files.py"]

L = {
    "en": {
        "subtitle": "Lesson and all exam questions", "sixty": "In 60 seconds", "traps": "Watch out",
        "questions": "All {n} exam questions of this topic", "sense": "common sense", "memo": "memorize",
        "meta": "{q} questions · about {p} of your 33 exam questions come from this topic · {m} to memorize, {s} common sense",
        "contents": "Contents", "video": "Video on this topic", "app": "This lesson in the study app",
        "foot": "Study files for the Einbürgerungstest (Bayern). Answers from the official BAMF catalog. "
                "The lesson and translations are study aids, not official texts.",
        "index": "All study files", "frage": "Frage",
    },
    "ru": {
        "subtitle": "Урок и все вопросы экзамена", "sixty": "За 60 секунд", "traps": "Осторожно",
        "questions": "Все {n} вопросов экзамена по этой теме", "sense": "здравый смысл", "memo": "запомнить",
        "meta": "{q} вопросов · в среднем {p} из 33 вопросов вашего экзамена из этой темы · запомнить: {m}, здравый смысл: {s}",
        "contents": "Содержание", "video": "Видео по этой теме", "app": "Этот урок в приложении",
        "foot": "Учебные материалы к Einbürgerungstest (Бавария). Ответы из официального каталога BAMF. "
                "Урок и переводы - учебная помощь, а не официальные тексты.",
        "index": "Все учебные файлы", "frage": "Frage",
    },
}

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--text:#1b1f24;--muted:#5d6673;--border:#d9dee5;--accent:#1f5fbf;--ok:#1f7a3a;--okbg:#e5f4ea;--warn:#8a5a00;--warnbg:#fff4d6}
*{box-sizing:border-box}
body{margin:0 auto;max-width:860px;padding:16px;font-family:system-ui,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.5}
h1{font-size:1.6rem;margin:4px 0}.sub{color:var(--muted);margin:0 0 8px}.meta{color:var(--muted);font-size:.9rem}
nav.toc{display:flex;flex-wrap:wrap;gap:4px 16px;margin:10px 0}nav.toc a{color:var(--accent)}
details{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 16px;margin:12px 0}
summary{cursor:pointer;font-weight:700;font-size:1.1rem;break-after:avoid;page-break-after:avoid}
.hook{border-left:3px solid var(--accent);padding-left:12px;font-size:1.05rem}
.traps{background:var(--warnbg);border-color:var(--warn)}
li{margin:6px 0}.q{color:var(--muted);font-size:.8rem;white-space:nowrap}.q.memo{color:var(--text);font-weight:600}.grey{color:var(--muted)}
.tag{font-size:.75rem;border:1px solid var(--border);border-radius:6px;padding:0 6px;color:var(--muted)}
.question{border-top:1px solid var(--border);padding:10px 0;break-inside:avoid;page-break-inside:avoid}
.question:first-of-type{border-top:none}
.de{font-weight:600}.tr{color:var(--muted)}.ans{color:var(--ok);font-weight:600;margin-top:4px}
.ans .tr{font-weight:400}
img{max-width:100%;height:auto;border:1px solid var(--border);border-radius:6px;background:#fff;margin:6px 0}
.links a{color:var(--accent)}footer{color:var(--muted);font-size:.8rem;margin:20px 0}
@media print{body{background:#fff;max-width:none;padding:0}details{border:none;padding:0;margin:8px 0}
 summary{list-style:none}summary::-webkit-details-marker{display:none}nav.toc,.links{display:none}}
@page{size:A4;margin:14mm}
"""

log = logging.getLogger("build_study_files")


def setup_logging() -> None:
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / "logs" / "build_study_files.log", encoding="utf-8")])


def load(name: str) -> dict | list:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def rich(text: str) -> str:
    """'a **b** c' -> 'a <b>b</b> c', escaped."""
    parts = html.escape(text).split("**")
    if len(parts) % 2 == 0:
        raise ValueError(f"unbalanced ** in: {text}")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def soft(text: str) -> str:
    """Escaped, with a line break allowed after every '/' (the catalog's long paired forms)."""
    return html.escape(text).replace("/", "/<wbr>")


def without_german(ru: str, de: str) -> str:
    """'бело-голубой (weiß-blau)' printed under the German 'weiß-blau': drop a bracket that only repeats the German."""
    m = re.fullmatch(r"(.*\S)\s*\(([^()]+)\)(\.?)", ru.strip())
    if m and m.group(2).casefold().rstrip(".") in de.casefold():
        return m.group(1) + m.group(3)
    return ru


def file_hash(rel: str) -> str:
    data = (ROOT / rel).read_bytes()
    if rel in TEXT_INPUTS:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def video_slugs() -> dict[str, str]:
    """lesson key -> video script slug, from the 'Lessons:' line of videos/scripts/*.md."""
    out = {}
    for p in sorted((ROOT / "videos" / "scripts").glob("*.md")):
        line = re.search(r"^Lessons?: (.+)$", p.read_text(encoding="utf-8"), re.M)
        if line is None:
            raise ValueError(f"{p.name} has no 'Lessons:' line")
        for key in re.findall(r"`([a-z_]+)`", line.group(1).split(" · ")[0]):
            out[key] = p.stem
    return out


def render_topic(n: int, topic: dict, lesson: dict, lang: str, q_by_id: dict, en: dict, ru: dict, video: str | None) -> str:
    t = L[lang]
    sense = set(lesson["common_sense"])
    qs = topic["questions"]
    points = sum(0.3 if q_by_id[i]["section"] == "Bayern" else 0.1 for i in qs)
    meta = t["meta"].format(q=len(qs), p=f"{points:.1f}", m=len(qs) - len(sense), s=len(sense))

    def qtags(ids: list[int]) -> str:
        return " ".join(f'<span class="q{"" if i in sense else " memo"}">Q{i}</span>' for i in ids)   # memorize dark, common sense grey (as in the app)

    sections = [("s-sixty", t["sixty"], "<ul>" + "".join(f"<li>{rich(s)}</li>" for s in lesson["summary"]) + "</ul>", "")]
    for i, sec in enumerate(lesson["sections"]):
        items = []
        for f in sec["facts"]:
            grey = all(q in sense for q in f["q"])
            tag = f' <span class="tag">{t["sense"]}</span>' if grey else ""
            items.append(f'<li class="{"grey" if grey else ""}">{rich(f["text"])}{tag} {qtags(f["q"])}</li>')
        sections.append((f"s{i + 1}", html.escape(sec["title"]), "<ul>" + "".join(items) + "</ul>", ""))
    if lesson["traps"]:
        sections.append(("s-traps", t["traps"], "<ul>" + "".join(f"<li>{rich(f['text'])} {qtags(f['q'])}</li>" for f in lesson["traps"]) + "</ul>", "traps"))
    blocks = []
    for i in qs:
        q = q_by_id[i]
        if lang == "en":
            tr_q, tr_a = en[str(i)]["question"], en[str(i)]["options"][q["answer_index"]]
        else:
            tr_q, tr_a = ru[str(i)]["question"], without_german(ru[str(i)]["answer"], q["answer"])
        img = ""
        if q["image"]:
            img = f'<img alt="{t["frage"]} {i}" src="data:image/png;base64,{base64.b64encode((ROOT / q["image"]).read_bytes()).decode()}">'
        kind = t["sense"] if i in sense else t["memo"]
        same = tr_a.strip().rstrip(".") == q["answer"].strip().rstrip(".")
        blocks.append(
            f'<div class="question"><div class="q">{t["frage"]} {i}{" (Bayern)" if q["section"] == "Bayern" else ""} · {kind}</div>'
            f'<div class="de" lang="de">{soft(q["question"])}</div><div class="tr">{soft(tr_q)}</div>{img}'
            f'<div class="ans">✓ <span lang="de">{soft(q["answer"])}</span>'
            f'{"" if same else f" <span class=tr>({soft(tr_a)})</span>"}</div></div>')
    sections.append(("s-questions", t["questions"].format(n=len(qs)), "".join(blocks), ""))

    toc = "".join(f'<a href="#{sid}">{title}</a>' for sid, title, _, _ in sections)
    body = "".join(f'<details open id="{sid}" class="{cls}"><summary>{title}</summary>{content}</details>' for sid, title, content, cls in sections)
    links = [f'<a href="{SITE}#/learn/{topic["key"]}">{t["app"]}</a>']
    if video:
        links.append(f'<a href="{SITE}#/read/{video}">{t["video"]}</a>')
    links.append(f'<a href="../index.html">{t["index"]}</a>')
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{n:02d} {html.escape(topic["title"])}</title><style>{CSS}</style></head><body>'
            f'<h1 lang="de">{n:02d} {html.escape(topic["title"])}</h1><p class="sub">{html.escape(topic["title_en"]) + " · " if lang == "en" else ""}{t["subtitle"]}</p>'
            f'<p class="meta">{meta}</p><p class="hook">{rich(lesson["hook"])}</p>'
            f'<nav class="toc" aria-label="{t["contents"]}">{toc}</nav>{body}'
            f'<p class="links">{" · ".join(links)}</p><footer>{t["foot"]}</footer></body></html>')


def render_index(rows: list[tuple[int, dict]]) -> str:
    trs = "".join(
        f'<tr><td>{n:02d}</td><td lang="de">{html.escape(tp["title"])}<div class="tr">{html.escape(tp["title_en"])}</div></td>'
        + "".join(f'<td><a href="{lang}/{n:02d}_{tp["key"]}.html">HTML</a> · <a href="{lang}/{n:02d}_{tp["key"]}.pdf">PDF</a></td>' for lang in LANGS)
        + "</tr>" for n, tp in rows)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Study files</title><style>{CSS}table{{width:100%;border-collapse:collapse;table-layout:fixed}}'
            f'col.n{{width:8%}}col.t{{width:52%}}col.l{{width:20%}}td,th{{border-top:1px solid var(--border);padding:8px 6px;text-align:left;vertical-align:top}}</style></head><body>'
            f'<h1>Einbürgerungstest (Bayern): study files</h1><p class="sub">One file per topic: the lesson and every exam question with its answer. '
            f'English or Russian, as HTML (phone) or PDF (print). Учебные файлы по каждой теме на английском и русском.</p>'
            f'<details open id="files"><summary>24 topics</summary><table><colgroup><col class="n"><col class="t"><col class="l"><col class="l"></colgroup>'
            f'<thead><tr><th>#</th><th>Topic</th><th>English</th><th>Русский</th></tr></thead><tbody>{trs}</tbody></table></details>'
            f'<p class="links"><a href="{SITE}">The study app</a></p></body></html>')


def main() -> None:
    setup_logging()
    t0 = time.time()
    if not CHROME.exists():
        raise FileNotFoundError(f"Chrome not found at {CHROME}: it prints the PDFs")
    topics = load("topics.json")["topics"]
    lessons = {l["topic"]: l for l in load("lessons.json")["lessons"]}
    ru_lessons = {l["topic"]: l for l in load("lessons_ru.json")["lessons"]}
    q_by_id = {q["id"]: q for q in load("questions_bayern.json")}
    en = load("translations_en.json")["translations"]
    ru = load("translations_ru.json")["translations"]
    videos = video_slugs()
    missing = [k for k in (str(i) for i in q_by_id) if k not in ru]
    if missing:
        raise ValueError(f"data/translations_ru.json lacks questions {missing[:10]}")

    def lesson_in(key: str, lang: str) -> dict:
        l = lessons[key]
        if lang == "en":
            return l
        r = ru_lessons[key]   # Russian text on the English structure (same checks as app/src/lib/lessons.ts)
        if len(r["sections"]) != len(l["sections"]) or len(r["traps"]) != len(l["traps"]):
            raise ValueError(f"data/lessons_ru.json: lesson {key} does not match data/lessons.json")
        return {**l, "hook": r["hook"], "summary": r["summary"],
                "sections": [{"title": rs["title"], "facts": [{**f, "text": rt} for f, rt in zip(s["facts"], rs["facts"], strict=True)]}
                             for s, rs in zip(l["sections"], r["sections"], strict=True)],
                "traps": [{**f, "text": rt} for f, rt in zip(l["traps"], r["traps"], strict=True)]}

    jobs = [(n, tp, lang) for lang in LANGS for n, tp in enumerate(topics, 1)]
    files = []
    for k, (n, tp, lang) in enumerate(jobs, 1):
        d = OUT / lang
        d.mkdir(parents=True, exist_ok=True)
        page = d / f"{n:02d}_{tp['key']}.html"
        page.write_text(render_topic(n, tp, lesson_in(tp["key"], lang), lang, q_by_id, en, ru, videos.get(tp["key"])), encoding="utf-8")
        pdf = page.with_suffix(".pdf")
        r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                            page.resolve().as_uri()], capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not pdf.exists() or pdf.read_bytes()[:4] != b"%PDF":
            raise RuntimeError(f"Chrome did not print {pdf.name}: {r.stderr[-400:]}")
        files += [page.relative_to(ROOT).as_posix(), pdf.relative_to(ROOT).as_posix()]
        elapsed = time.time() - t0
        log.info(f"{k}/{len(jobs)} {lang}/{page.stem}: {page.stat().st_size // 1024} KB html, {pdf.stat().st_size // 1024} KB pdf, "
                 f"{elapsed:.0f}s elapsed, ~{elapsed / k * (len(jobs) - k):.0f}s left")
    (OUT / "index.html").write_text(render_index(list(enumerate(topics, 1))), encoding="utf-8")
    images = sorted(p.relative_to(ROOT).as_posix() for p in (DATA / "images").glob("*.png"))
    manifest = {"description": "Written by scripts/build_study_files.py. app/vite.config.ts compares these hashes with the inputs "
                               "and refuses to publish the study files if an input changed (text inputs hashed with LF line ends).",
                "text_inputs": TEXT_INPUTS, "binary_inputs": images,
                "inputs": {rel: file_hash(rel) for rel in TEXT_INPUTS + images},
                "files": files + ["study/index.html"]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    log.info(f"wrote {len(files)} files + index to {OUT.relative_to(ROOT)} in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
