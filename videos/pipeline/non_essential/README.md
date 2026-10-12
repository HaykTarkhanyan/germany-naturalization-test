# videos/pipeline/non_essential

Tools around the renderer that are not needed to make a video. Moved here from the session scratchpad on 2026-10-12,
together with `../render.py` and `../tts.py` (DECISIONS.md #22).

| Script | What it does | When to re-run it |
|---|---|---|
| `check_scripts.py` | Checks every video script without API calls: fields, `{Q}` markers vs the Questions line in both languages, cards = the lessons' questions, no memorize question only in the recap, no dashes or curly quotes, every subtitle and big term card fits; logs estimated durations (`--write` puts them into the scripts) | After editing a script, before voicing or rendering it |
| `listen_page.py` | Writes `videos/build/index.html`: all rendered videos, Russian and English side by side, playing from `videos/mp4/` | After rendering, to watch the series on this machine |
