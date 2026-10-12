# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "google-genai==2.29.0",
#     "pillow==12.3.0",
# ]
# ///
"""Render the explainer videos: videos/scripts/NN_slug.md -> videos/mp4/NN_slug.{ru,en}.mp4.

Each scene is voiced once by Gemini TTS (voice Charon, calm style; tts.py) and cached in videos/build/render/<video>.<lang>/
as sN.wav plus sN.txt, the exact text that was voiced. A clip is reused only while sN.txt equals the scene's current
text, so an edited script line never plays old audio. Making audio costs money, so it happens only with --tts; without
it a render that needs new audio stops and says which scenes and roughly what they cost. Frames are static Pillow
images (exam cards with German + English, correct option green, subtitles), joined by ffmpeg.

Needs: ffmpeg on PATH, Windows fonts (Segoe UI), and for --tts Google application-default credentials for the Vertex
project in .env. Cost ledger: videos/build/costs.json (ignored, like the whole build folder).

Run:      uv run videos/pipeline/render.py 12_ddr ru        (one video, one language)
          uv run videos/pipeline/render.py 12_ddr           (both languages)
          uv run videos/pipeline/render.py all              (all 14 videos, both languages)
          add --tts to make missing audio
Runtime:  ~1 min per video and language from cached audio (frames ~15 s, encode 20-55 s), ~30 min for all 28;
          new audio adds ~5-10 s per scene
Cost:     $0 from cached audio; new audio ~$0.005 per scene (voice + transcription check), ~$0.05 per video and language
"""

import argparse
import json
import logging
import re
import subprocess
import time
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "videos" / "scripts"
MP4 = REPO / "videos" / "mp4"
WORK = REPO / "videos" / "build" / "render"
LANGS = ("ru", "en")
W, H = 1280, 720
GAP_S = 0.45          # pause between scenes
CARD_MIN_S = 3.0      # the last card of a scene stays up at least this long (plus 1 s per extra card in a grid)
GRID_GAP_S = 2.0      # cards revealed less than this apart share one grid (a card shown for less is unreadable)
SUB_SPLIT = 95        # a sentence longer than this is split at its last ", " before this many characters
SUB_SHORT = 40        # a piece shorter than this ("To memorize:", "1945.") is joined to its neighbour ...
SUB_JOIN = 150        # ... while the joined subtitle stays this short (about two lines)
SUB_LINES = 3         # more lines than this fails the render (they would be cut off)
VOICE = "Charon"
# Hayk picked Charon with this style on 2026-10-06 (DECISIONS.md #16).
STYLE = "calm, clear and friendly teacher's voice"
ATTEMPTS = 3          # voice attempts per scene before the render stops
COST_PER_SCENE = 0.005

FONTS = "C:/Windows/Fonts/"
SYM = ImageFont.truetype(FONTS + "seguisym.ttf", 30)
QUESTIONS = {q["id"]: q for q in json.loads((REPO / "data" / "questions_bayern.json").read_text(encoding="utf-8"))}
ENGLISH = json.loads((REPO / "data" / "translations_en.json").read_text(encoding="utf-8"))["translations"]
MARKS = json.loads((REPO / "videos" / "image_marks.json").read_text(encoding="utf-8"))["marks"]

log = logging.getLogger("render")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTS + ("segoeuib.ttf" if bold else "segoeui.ttf"), size)


# ---------- script ----------
def load_script(slug: str, lang: str) -> tuple[str, list[dict]]:
    """The video's title (from "# NN Title") and its scenes in one language."""
    src = (SCRIPTS / f"{slug}.md").read_text(encoding="utf-8")
    head = re.search(r"^# (.+)$", src, re.M)
    if head is None:
        raise RuntimeError(f"videos/scripts/{slug}.md has no '# NN Title' line")
    scenes = []
    for block in src.split("\n## ")[1:]:
        title = block.split("\n", 1)[0]
        f = {m.group(1): m.group(2).strip() for m in re.finditer(r"- \*\*(Voice RU|Voice EN|On screen|Visual|Questions):\*\* (.*)", block)}
        missing = {f"Voice {lang.upper()}", "On screen", "Visual"} - set(f)
        if missing:
            raise RuntimeError(f"videos/scripts/{slug}.md scene '{title}' has no {sorted(missing)}")
        voice = f[f"Voice {lang.upper()}"]
        scenes.append({"title": title, "voice": voice, "screen": f["On screen"], "visual": f["Visual"],
                       "text": re.sub(r"\s*\{Q\d+\}\s*", " ", voice).strip()})
    return head.group(1).split(" ", 1)[1], scenes


# ---------- voice ----------
def cached(work: Path, i: int, text: str) -> bool:
    wav, txt = work / f"s{i + 1}.wav", work / f"s{i + 1}.txt"
    return wav.exists() and txt.exists() and txt.read_text(encoding="utf-8") == text


def make_audio(text: str, work: Path, i: int, slug: str, lang: str) -> None:
    """Voice one scene and keep it only if the transcription matches the text. A failed attempt is kept as
    sN.failedK.wav and logged with its cost; after ATTEMPTS failures the render stops."""
    import tts   # creates the Vertex client: only when audio is really made

    wav = work / f"s{i + 1}.wav"
    for n in range(1, ATTEMPTS + 1):
        data, secs, e = tts.speak(text, VOICE, STYLE, "ru-RU" if lang == "ru" else None)
        said, c = tts.check(text, data)
        e.update({"lang": lang, "file": wav.relative_to(REPO).as_posix(), "purpose": f"render {slug}.{lang}", "check_overlap": c["overlap"], "attempt": n})
        c.update({"file": e["file"], "purpose": f"render {slug}.{lang} check"})
        tts.append_ledger([e, c])
        if c["ok"]:
            wav.write_bytes(data)
            wav.with_suffix(".transcript.txt").write_text(said, encoding="utf-8")
            (work / f"s{i + 1}.txt").write_text(text, encoding="utf-8")
            log.info(f"  scene {i + 1}: {secs:.1f} s of audio, transcript match {c['overlap']:.0%}, attempt {n}, ${e['cost_usd_if_paid'] + c['cost_usd_if_paid']:.4f}")
            return
        bad = wav.with_name(f"{wav.stem}.failed{n}.wav")
        bad.write_bytes(data)
        log.warning(f"  scene {i + 1} attempt {n} failed (overlap {c['overlap']:.0%}, {c['extra_words']:+d} words), kept as {bad.name}: {said[:120]}")
    raise RuntimeError(f"{slug}.{lang} scene {i + 1}: {ATTEMPTS} attempts did not match the text: {text}")


def wav_seconds(p: Path) -> float:
    with wave.open(str(p), "rb") as w:
        return w.getnframes() / w.getframerate()


# ---------- timing ----------
def chunks(text: str) -> list[str]:
    """Subtitles: split at sentence ends, colons and semicolons (recap lists are one long sentence), split what is
    still too long at a comma, then join short pieces to a neighbour so nothing flashes by for under a second."""
    pieces = []
    for p in re.split(r"(?<=[.!?:;])\s+", text):
        while len(p) > SUB_SPLIT:
            cut = p.rfind(", ", 0, SUB_SPLIT)
            if cut < 30:
                break
            pieces.append(p[:cut + 1])
            p = p[cut + 2:]
        pieces.append(p)
    out: list[str] = []
    for p in filter(None, pieces):
        if out and (len(out[-1]) < SUB_SHORT or len(p) < SUB_SHORT) and len(out[-1]) + 1 + len(p) <= SUB_JOIN:
            out[-1] += " " + p
        else:
            out.append(p)
    return out


def time_scene(sc: dict) -> None:
    """Card and subtitle times: a {Q} marker's position in the text, scaled to the clip's length."""
    text, d = sc["text"], sc["audio_s"]
    marks = []
    for m in re.finditer(r"\{Q(\d+)\}", sc["voice"]):
        before = re.sub(r"\s*\{Q\d+\}\s*", " ", sc["voice"][:m.start()]).strip()
        marks.append((len(before) / len(text) * d, int(m.group(1))))
    events, last_t = [], None
    for t, q in marks:
        if events and t - last_t < GRID_GAP_S:
            events[-1] = (events[-1][0], events[-1][1] + (q,))
        else:
            events.append((t, (q,)))
        last_t = t
    sc["cards"] = events
    last_min = CARD_MIN_S + 1.0 * (len(events[-1][1]) - 1) if events else 0
    sc["duration"] = max(d, (events[-1][0] + last_min) if events else d)
    subs, t = [], 0.0
    for c in chunks(text):
        dt = len(c) / len(text) * d
        subs.append((t, t + dt, c))
        t += dt
    sc["subs"] = subs


# ---------- drawing ----------
def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def background() -> Image.Image:
    # Hayk 2026-10-06: no web photos needed, the question and answer are the content. Plain background.
    bg = Image.new("RGB", (W, H), (18, 24, 33))
    d = ImageDraw.Draw(bg)
    for y in range(H):  # subtle vertical gradient
        d.line([(0, y), (W, y)], fill=(18 + y // 40, 24 + y // 30, 40 + y // 20))
    return bg


def panel(img: Image.Image, box: tuple, fill: tuple, radius: int = 18, outline: tuple | None = None, width: int = 0) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)
    img.alpha_composite(layer)


def term_card(img: Image.Image, text: str, y_center: int, size: int, max_lines: int = 3) -> bool:
    """The scene's key terms; False (nothing drawn) if they need more than max_lines."""
    d = ImageDraw.Draw(img)
    fnt = font(size, True)
    lines = wrap(d, text, fnt, W - 260)
    if len(lines) > max_lines:
        return False  # e.g. above an exam card: no room, and the card shows the facts anyway
    lh = size + 10
    h = lh * len(lines) + 30
    top = y_center - h // 2
    panel(img, (100, top, W - 100, top + h), (10, 14, 20, 190))
    for i, l in enumerate(lines):
        d.text((W // 2, top + 15 + i * lh + lh // 2), l, font=fnt, fill=(255, 255, 255), anchor="mm")
    return True


def exam_card(img: Image.Image, qid: int, top: int = 128, bottom: int = 590) -> None:
    """The exam question as on the sheet (German, catalog order), English under the question and after each
    option, correct option green with a check mark, green box on the right picture (videos/image_marks.json)."""
    q, en = QUESTIONS[qid], ENGLISH[str(qid)]
    d = ImageDraw.Draw(img)
    x0, x1 = 70, W - 70
    panel(img, (x0, top, x1, bottom), (250, 251, 253, 248))
    d.text((x0 + 24, top + 14), f"Frage {qid}" + (" · Bayern" if q["section"] == "Bayern" else ""), font=font(19), fill=(93, 102, 115))
    qf, ef = font(25, True), font(20)
    y = top + 42
    for l in wrap(d, q["question"], qf, x1 - x0 - 48)[:2]:
        d.text((x0 + 24, y), l, font=qf, fill=(27, 31, 36))
        y += 32
    for l in wrap(d, en["question"], ef, x1 - x0 - 48)[:2]:
        d.text((x0 + 24, y), l, font=ef, fill=(93, 102, 115))
        y += 26
    y += 10
    ox = x0 + 24
    if q["image"]:
        pic = Image.open(REPO / q["image"]).convert("RGB")
        s = min(430 / pic.width, (bottom - y - 20) / pic.height)
        pw, ph = int(pic.width * s), int(pic.height * s)
        pic = pic.resize((pw, ph))
        img.paste(pic, (ox, y))
        if str(qid) in MARKS:
            a, b, c, e = MARKS[str(qid)]
            ImageDraw.Draw(img).rounded_rectangle((ox + a * s - 4, y + b * s - 4, ox + c * s + 4, y + e * s + 4), 8, outline=(31, 160, 70), width=5)
        ox += pw + 28
    ow = x1 - 24 - ox
    oy = y
    oh = (bottom - 18 - y) // 4 - 10
    for i, opt in enumerate(q["options"]):
        ok = i == q["answer_index"]
        box = (ox, oy, ox + ow, oy + oh)
        panel(img, box, (229, 244, 234, 255) if ok else (255, 255, 255, 255), radius=10,
              outline=(31, 122, 58) if ok else (217, 222, 229), width=3 if ok else 2)
        d = ImageDraw.Draw(img)
        d.text((ox + 16, oy + oh // 2), "ABCD"[i], font=font(23, True), fill=(31, 122, 58) if ok else (93, 102, 115), anchor="lm")
        # German option, then its English translation in grey on the same line (wrapping to a second line if long)
        de_font, en_font = font(22, ok), font(19)
        de_w, en_txt = d.textlength(opt, font=de_font), "  " + en["options"][i]
        tx, ty, maxw = ox + 52, oy + oh // 2, ow - 100
        if opt == en["options"][i]:          # e.g. "4" -> nothing to translate
            d.text((tx, ty), opt, font=de_font, fill=(27, 31, 36), anchor="lm")
        elif de_w + d.textlength(en_txt, font=en_font) <= maxw:
            d.text((tx, ty), opt, font=de_font, fill=(27, 31, 36), anchor="lm")
            d.text((tx + de_w, ty + 1), en_txt, font=en_font, fill=(93, 102, 115), anchor="lm")
        else:
            d.text((tx, ty - 12), wrap(d, opt, de_font, maxw)[0], font=de_font, fill=(27, 31, 36), anchor="lm")
            d.text((tx, ty + 14), wrap(d, en["options"][i], en_font, maxw)[0], font=en_font, fill=(93, 102, 115), anchor="lm")
        if ok:
            d.text((ox + ow - 22, oy + oh // 2), "\u2713", font=SYM, fill=(31, 122, 58), anchor="rm")
        oy += oh + 10


def exam_grid(img: Image.Image, qids: tuple, top: int = 128, bottom: int = 590) -> None:
    """Several questions answered together: the shared question once, then a small card per question with its
    options (German, English after it) and the correct one green. Picture questions are not expected here."""
    qs = [QUESTIONS[q] for q in qids]
    if any(q["image"] for q in qs):
        raise NotImplementedError(f"picture question in a card grid: {qids}")
    d = ImageDraw.Draw(img)
    x0, x1 = 70, W - 70
    panel(img, (x0, top, x1, bottom), (250, 251, 253, 248))
    same = len({q["question"] for q in qs}) == 1
    y = top + 14
    if same:
        d.text((x0 + 24, y), "Fragen " + ", ".join(str(q) for q in qids), font=font(19), fill=(93, 102, 115))
        y += 28
        for l in wrap(d, qs[0]["question"], font(23, True), x1 - x0 - 48)[:2]:
            d.text((x0 + 24, y), l, font=font(23, True), fill=(27, 31, 36))
            y += 30
        for l in wrap(d, ENGLISH[str(qids[0])]["question"], font(18), x1 - x0 - 48)[:1]:
            d.text((x0 + 24, y), l, font=font(18), fill=(93, 102, 115))
            y += 26
        y += 6
    cols = 3 if len(qids) > 4 else 2
    rows = -(-len(qids) // cols)
    gap = 14
    cw = (x1 - x0 - 48 - gap * (cols - 1)) // cols
    ch = (bottom - 16 - y - gap * (rows - 1)) // rows
    for n, (qid, q) in enumerate(zip(qids, qs)):
        cx = x0 + 24 + (n % cols) * (cw + gap)
        cy = y + (n // cols) * (ch + gap)
        panel(img, (cx, cy, cx + cw, cy + ch), (255, 255, 255, 255), radius=10, outline=(217, 222, 229), width=2)
        d = ImageDraw.Draw(img)
        ty = cy + 8
        d.text((cx + 10, ty), f"Frage {qid}", font=font(15), fill=(93, 102, 115))
        ty += 20
        if not same:  # each card shows its own question, up to two lines
            for l in wrap(d, q["question"], font(14, True), cw - 20)[:2]:
                d.text((cx + 10, ty), l, font=font(14, True), fill=(27, 31, 36))
                ty += 17
            ty += 3
        oh = (cy + ch - 6 - ty) // 4
        en = ENGLISH[str(qid)]["options"]
        for i, opt in enumerate(q["options"]):
            ok = i == q["answer_index"]
            if ok:
                panel(img, (cx + 6, ty, cx + cw - 6, ty + oh - 3), (229, 244, 234, 255), radius=6, outline=(31, 122, 58), width=2)
                d = ImageDraw.Draw(img)
            room = cw - 64   # letter on the left, check mark on the right
            label = opt if opt == en[i] else f"{opt}  ({en[i]})"
            if d.textlength(label, font=font(16, ok)) > room:
                label = opt   # the English goes first when there is no room
            while d.textlength(label, font=font(16, ok)) > room and len(label) > 8:
                label = label[:-2]
            d.text((cx + 14, ty + (oh - 3) // 2), "ABCD"[i] + "  " + label, font=font(16, ok), fill=(27, 31, 36), anchor="lm")
            if ok:
                d.text((cx + cw - 14, ty + (oh - 3) // 2), "✓", font=SYM, fill=(31, 122, 58), anchor="rm")
            ty += oh


def subtitle_lines(text: str) -> list[str]:
    lines = wrap(ImageDraw.Draw(Image.new("RGB", (1, 1))), text, font(28), W - 220)
    if len(lines) > SUB_LINES:
        raise RuntimeError(f"subtitle needs {len(lines)} lines, the box shows {SUB_LINES}: {text}")
    return lines


def subtitle(img: Image.Image, text: str) -> None:
    d = ImageDraw.Draw(img)
    fnt = font(28)
    lines = subtitle_lines(text)
    h = 38 * len(lines) + 20
    top = H - h - 22
    panel(img, (80, top, W - 80, H - 22), (0, 0, 0, 175), radius=12)
    for i, l in enumerate(lines):
        d.text((W // 2, top + 10 + i * 38 + 19), l, font=fnt, fill=(255, 255, 255), anchor="mm")


def frame(sc: dict, idx: int, n_scenes: int, title: str, card: tuple | None, sub: str | None) -> Image.Image:
    img = background().convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((28, 22), f"Einbürgerungstest · {title}", font=font(20), fill=(230, 235, 240))
    d.text((W - 28, 22), f"{idx + 1}/{n_scenes}", font=font(20), fill=(230, 235, 240), anchor="ra")
    if card is None:
        if sc["visual"].startswith("exam:"):  # exam picture scene before its card appears: show the picture
            pic = Image.open(REPO / QUESTIONS[int(sc["visual"].split(":")[1].split()[0])]["image"]).convert("RGB")
            s = min(760 / pic.width, 330 / pic.height)
            pic = pic.resize((int(pic.width * s), int(pic.height * s)))
            img.paste(pic, ((W - pic.width) // 2, 230))
            term_card(img, sc["screen"], 140, 34)
        else:  # no exam card: the term card is the content, so shrink it until it fits (a long recap list), never skip it
            if not any(term_card(img, sc["screen"], 300, size, max_lines=n) for size, n in ((44, 3), (36, 5), (30, 7))):
                raise RuntimeError(f"term card does not fit even at 30 px: {sc['screen']}")
    else:
        term_card(img, sc["screen"], 92, 26, max_lines=1)
        if len(card) == 1:
            exam_card(img, card[0])
        else:
            exam_grid(img, card)
    if sub:
        subtitle(img, sub)
    return img.convert("RGB")


# ---------- one video ----------
def render(slug: str, lang: str, allow_tts: bool, work: Path | None = None, out: Path | None = None) -> Path:
    work = work or WORK / f"{slug}.{lang}"
    out = out or MP4 / f"{slug}.{lang}.mp4"
    work.mkdir(parents=True, exist_ok=True)
    title, scenes = load_script(slug, lang)
    need = [i for i, sc in enumerate(scenes) if not cached(work, i, sc["text"])]
    if need and not allow_tts:
        raise RuntimeError(f"{slug}.{lang}: scenes {[i + 1 for i in need]} have no audio for their current text; "
                           f"rerun with --tts (about ${COST_PER_SCENE * len(need):.2f})")
    for i in need:
        make_audio(scenes[i]["text"], work, i, slug, lang)
    for i, sc in enumerate(scenes):
        sc["audio_s"] = wav_seconds(work / f"s{i + 1}.wav")
        time_scene(sc)

    frames_dir = work / "frames"
    frames_dir.mkdir(exist_ok=True)
    concat, audio_parts, n = [], [], 0
    for i, sc in enumerate(scenes):
        d = sc["duration"]
        cuts = sorted({0.0, d, *[t for t, _ in sc["cards"]], *[s for s, _, _ in sc["subs"]], *[e for _, e, _ in sc["subs"] if e < d]})
        for a, b in zip(cuts, cuts[1:]):
            if b - a < 0.05:
                continue
            mid = (a + b) / 2
            card = next((q for t, q in reversed(sc["cards"]) if t <= mid), None)
            sub = next((c for s, e, c in sc["subs"] if s <= mid < e), None)
            p = frames_dir / f"f{n:04d}.png"
            frame(sc, i, len(scenes), title, card, sub).save(p)
            n += 1
            concat.append((p, b - a))
        # pause between scenes: hold the scene's last look without subtitle
        p = frames_dir / f"f{n:04d}.png"
        frame(sc, i, len(scenes), title, sc["cards"][-1][1] if sc["cards"] else None, None).save(p)
        n += 1
        concat.append((p, GAP_S))
        audio_parts.append((work / f"s{i + 1}.wav", d - sc["audio_s"] + GAP_S))

    # audio: the scene clips with padding silence
    full = work / "voice.wav"
    with wave.open(str(full), "wb") as dst:
        dst.setnchannels(1)
        dst.setsampwidth(2)
        dst.setframerate(24000)
        for path, pad in audio_parts:
            with wave.open(str(path), "rb") as w:
                if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (24000, 1, 2):
                    raise RuntimeError(f"{path}: unexpected format")
                dst.writeframes(w.readframes(w.getnframes()))
            dst.writeframes(b"\x00\x00" * int(pad * 24000))

    lst = work / "frames.txt"
    with open(lst, "w", encoding="utf-8") as fh:
        for p, d in concat:
            fh.write(f"file '{p.as_posix()}'\nduration {d:.3f}\n")
        fh.write(f"file '{concat[-1][0].as_posix()}'\n")
    # Encode next to the frames, then move: a failed encode never leaves a broken file in videos/mp4/.
    tmp = work / "video.mp4"
    t0 = time.time()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(full),
                    "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-threads", "2", "-r", "25", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(tmp)], check=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp.replace(out)
    log.info(f"{out.name}: {sum(d for _, d in concat):.1f} s, {n} frames, {out.stat().st_size / 1e6:.1f} MB, encode {time.time() - t0:.1f} s")
    return out


def setup_logging() -> None:
    (REPO / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(REPO / "logs" / "render.log", encoding="utf-8")])


def main() -> None:
    ap = argparse.ArgumentParser(description="Render explainer videos from videos/scripts/ into videos/mp4/.")
    ap.add_argument("video", help="script name without .md (e.g. 12_ddr), or 'all'")
    ap.add_argument("lang", nargs="?", choices=LANGS, help="one language (default: both)")
    ap.add_argument("--tts", action="store_true", help="make missing audio with Gemini TTS (costs money, see the docstring)")
    args = ap.parse_args()
    setup_logging()
    slugs = sorted(p.stem for p in SCRIPTS.glob("*.md")) if args.video == "all" else [args.video]
    for s in slugs:
        if not (SCRIPTS / f"{s}.md").exists():
            raise SystemExit(f"no script videos/scripts/{s}.md")
    jobs = [(s, lang) for s in slugs for lang in ([args.lang] if args.lang else LANGS)]
    t0 = time.time()
    for k, (slug, lang) in enumerate(jobs, 1):
        log.info(f"== {k}/{len(jobs)} {slug}.{lang}")
        render(slug, lang, args.tts)
        elapsed = time.time() - t0
        log.info(f"{k}/{len(jobs)} done, {elapsed:.0f}s elapsed, ~{elapsed / k * (len(jobs) - k):.0f}s left")
    log.info(f"rendered {len(jobs)} videos in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
