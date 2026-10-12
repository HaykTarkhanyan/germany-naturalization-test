"""Voice and transcription check for the video renderer (render.py), plus the cost ledger.

Gemini TTS runs on Vertex AI with Google application-default credentials for the project in .env
(GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION), where the trial credit is (DECISIONS.md #17). The style goes in
Part.speech_metadata, never into the text: gemini-3.8-flash-tts reads its input verbatim (an instruction prefix was
spoken aloud in the first demo). Every clip is transcribed and compared with the text, because the voice sometimes
speaks a Russian line in German or Ukrainian with no error (_learnings/2026-10-12-0010_tts-language-drift.md).
Importing this module creates the Vertex client, so render.py imports it only when audio has to be made.
"""

import io
import json
import re
import time
import wave
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "videos" / "build" / "costs.json"
TTS_MODEL, STT_MODEL = "gemini-3.8-flash-tts", "gemini-3.1-flash-lite"
TTS_IN, TTS_OUT = 0.50e-6, 9.00e-6   # $/token, paid tier through 2026-12-31 (ai.google.dev/gemini-api/docs/pricing, read 2026-10-06)
STT_IN, STT_OUT = 0.50e-6, 1.50e-6   # gemini-3.1-flash-lite: audio input, text output
MATCH = 0.8   # all correct scenes scored >= 83%; one that switched to German mid-sentence 70%, Ukrainian 39%

_env = dict(l.strip().split("=", 1) for l in (REPO / ".env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
client = genai.Client(vertexai=True, project=_env["GOOGLE_CLOUD_PROJECT"], location=_env["GOOGLE_CLOUD_LOCATION"])


def append_ledger(entries: list[dict]) -> None:
    """Re-read the ledger before every write: two renders that each kept their own copy overwrote each other's entries once."""
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else []
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(ledger + entries, ensure_ascii=False, indent=1), encoding="utf-8")


def speak(text: str, voice: str, style: str | None, language_code: str | None) -> tuple[bytes, float, dict]:
    """One WAV clip (24 kHz mono 16-bit, returned complete with its header). language_code "ru-RU" makes Ukrainian
    less likely but does not prevent it; the transcription check is what catches it."""
    t0 = time.time()
    part = types.Part(text=text, speech_metadata=types.SpeechMetadata(style=style) if style else None)
    r = client.models.generate_content(model=TTS_MODEL, contents=[types.Content(role="user", parts=[part])], config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(language_code=language_code, voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
    data = b"".join(p.inline_data.data for p in r.candidates[0].content.parts if p.inline_data and p.inline_data.data)
    if data[:4] != b"RIFF":
        raise RuntimeError(f"expected a WAV file from {TTS_MODEL}, got {r.candidates[0].content.parts[0].inline_data.mime_type}")
    with wave.open(io.BytesIO(data)) as w:
        secs = w.getnframes() / w.getframerate()
    u = r.usage_metadata
    return data, secs, {"at": datetime.now().isoformat(timespec="seconds"), "model": TTS_MODEL, "api": "vertex", "voice": voice,
                        "style": f"Part.speech_metadata: {style}" if style else "plain",
                        "chars": len(text), "words": len(text.split()), "audio_s": round(secs, 2), "wpm": round(len(text.split()) / secs * 60),
                        "wall_s": round(time.time() - t0, 1), "prompt_tokens": u.prompt_token_count, "output_tokens": u.candidates_token_count,
                        "cost_usd_if_paid": round(u.prompt_token_count * TTS_IN + u.candidates_token_count * TTS_OUT, 5)}


def words(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower().replace("ё", "е"))


def check(text: str, data: bytes) -> tuple[str, dict]:
    """Transcribe the clip and compare it with the text; entry["ok"] says whether it matches."""
    r = client.models.generate_content(model=STT_MODEL, contents=[types.Part.from_bytes(data=data, mime_type="audio/wav"),
        "Transcribe this audio exactly, word for word, in the language spoken. Write German words and names in their "
        "German spelling with Latin letters. Write numbers as digits only if they are spoken as numbers. Output only the transcript."])
    said = r.text.strip()
    a, b = words(text), words(said)
    # In Russian text, German names and terms come back in arbitrary spelling (Helmut Kohl -> Гельмут Коль), so the
    # match is scored on the Cyrillic words only; the length check still counts every word.
    scored = [w for w in a if re.search(r"[а-я]", w)] or a
    overlap = sum(1 for w in scored if w in set(b)) / len(scored)
    extra = len(b) - len(a)
    u = r.usage_metadata
    return said, {"at": datetime.now().isoformat(timespec="seconds"), "model": STT_MODEL, "api": "vertex", "purpose": "transcription check",
                  "prompt_tokens": u.prompt_token_count, "output_tokens": u.candidates_token_count,
                  "cost_usd_if_paid": round(u.prompt_token_count * STT_IN + u.candidates_token_count * STT_OUT, 5),
                  "overlap": round(overlap, 2), "extra_words": extra,
                  "ok": not (extra > max(3, 0.15 * len(a)) or overlap < MATCH)}
