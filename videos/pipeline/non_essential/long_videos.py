"""Join the 14 explainer videos of each language into one long video for YouTube, with chapter timestamps.

videos/mp4/NN_*.en.mp4 -> videos/build/youtube/einbuergerungstest_bayern_en.mp4 (same for ru), in study order 01-14,
plus videos/build/youtube/timestamps.txt with one YouTube chapter line per part ("0:00 01 Bayern - Bavaria").
The streams are copied, not re-encoded (all parts come from videos/pipeline/render.py with identical settings, which
is checked first), so there is no quality loss. A chapter starts where the previous parts end (their measured
durations), and each chapter start is checked: the long video's frame 0.5 s into a chapter must equal the part's own
frame at 0.5 s.

Needs: ffmpeg and ffprobe on PATH, Pillow for the frame check.
Run:      uv run --with pillow==12.3.0 python videos/pipeline/non_essential/long_videos.py
Runtime:  ~1 min (measured 57 s: copying ~117 MB, plus 28 frame checks)
"""

import io
import logging
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageChops

REPO = Path(__file__).resolve().parents[3]
MP4 = REPO / "videos" / "mp4"
OUT = REPO / "videos" / "build" / "youtube"
SCRIPTS = REPO / "videos" / "scripts"

# Chapter names: the German title (the exam's language) and a short gloss.
GLOSS = {
    "en": ["Bavaria", "The Wall and reunification", "After the war", "Federal elections in practice", "Chancellor and President",
           "The two chambers of parliament", "Basic Law, basic rights, rule of law", "Elections and parties",
           "Federation, states, municipalities and courts", "Welfare state and work", "Nazi era, war and remembrance", "The GDR",
           "Germany and Europe", "Everyday life: family, school, religion, authorities"],
    "ru": ["Бавария", "Стена и воссоединение", "Послевоенное время", "Выборы в бундестаг на практике", "Канцлер и президент",
           "Бундестаг и бундесрат", "Основной закон, основные права, правовое государство", "Выборы и партии",
           "Федерация, земли, общины и суды", "Социальное государство и работа", "Нацизм, война и память", "ГДР",
           "Германия и Европа", "Повседневная жизнь: семья, школа, религия, ведомства"],
}

log = logging.getLogger("long_videos")


def probe(path: Path, entries: str, stream: str | None = None) -> str:
    cmd = ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "csv=p=0", str(path)]
    if stream:
        cmd[3:3] = ["-select_streams", stream]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def frame_at(path: Path, t: float) -> Image.Image:
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB")


def clock(seconds: float, hours: bool) -> str:
    s = int(seconds)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if hours else f"{s // 60}:{s % 60:02d}"


def main() -> None:
    (REPO / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(REPO / "logs" / "long_videos.log", encoding="utf-8")])
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    slugs = sorted(p.stem for p in SCRIPTS.glob("*.md"))
    titles = [(SCRIPTS / f"{s}.md").read_text(encoding="utf-8").split("\n", 1)[0].removeprefix("# ") for s in slugs]
    if len(slugs) != len(GLOSS["en"]):
        raise ValueError(f"{len(slugs)} scripts but {len(GLOSS['en'])} chapter glosses: update GLOSS")
    lines = []
    for lang in ("en", "ru"):
        parts = [MP4 / f"{s}.{lang}.mp4" for s in slugs]
        missing = [p.name for p in parts if not p.exists()]
        if missing:
            raise FileNotFoundError(f"missing {missing}: render them with videos/pipeline/render.py")
        settings = {probe(p, "stream=codec_name,width,height,r_frame_rate,sample_rate,channels,pix_fmt").replace("\n", "|") for p in parts}
        if len(settings) != 1:
            raise ValueError(f"{lang}: parts differ in codec settings, a stream copy would break: {settings}")
        durations = [float(probe(p, "format=duration")) for p in parts]
        starts = [sum(durations[:i]) for i in range(len(parts))]
        lst = OUT / f"parts_{lang}.txt"
        lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        out = OUT / f"einbuergerungstest_bayern_{lang}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                        "-movflags", "+faststart", str(out)], check=True)
        total = float(probe(out, "format=duration"))
        if abs(total - sum(durations)) > 1.0:
            raise RuntimeError(f"{out.name}: {total:.1f} s long, the parts add up to {sum(durations):.1f} s")
        for i, (p, start) in enumerate(zip(parts, starts)):   # chapter starts land on each part's first frames
            diff = ImageChops.difference(frame_at(out, start + 0.5), frame_at(p, 0.5))
            worst = max(hi for _, hi in diff.getextrema())
            if worst > 8:
                raise RuntimeError(f"{out.name}: chapter {i + 1} at {start:.2f} s does not show {p.name} (pixel difference {worst})")
        hours = total >= 3600
        lines.append(f"== {out.name} ({clock(total, True)}, {out.stat().st_size / 1e6:.0f} MB)")
        lines += [f"{clock(s, hours)} {t} - {g}" for s, t, g in zip(starts, titles, GLOSS[lang])]
        lines.append("")
        log.info(f"{out.name}: {len(parts)} parts, {total / 60:.1f} min, {out.stat().st_size / 1e6:.0f} MB, all chapter starts checked")
    (OUT / "timestamps.txt").write_text("\n".join(lines), encoding="utf-8")
    log.info("timestamps:\n" + "\n".join(lines))
    log.info(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
