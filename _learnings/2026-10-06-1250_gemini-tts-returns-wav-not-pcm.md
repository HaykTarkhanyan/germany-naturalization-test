# Gemini 3.8 Flash TTS (AI Studio) returns a complete WAV file, not raw PCM

**Symptom:** The first voice samples (2026-10-06) had a second WAV header inside the audio data: wrapping the
response bytes in `wave.open(...).writeframes()` produced a file whose first "samples" were the bytes `RIFF...`,
heard as a click at the start.

**Cause:** Most examples (and the Gemini 2.5 TTS docs) treat the response as raw 16-bit PCM at 24 kHz and wrap
it. `gemini-3.8-flash-tts` via google-genai 2.28.0 returns `inline_data.mime_type == "audio/wav"` and the data
already starts with `RIFF` (inner header: 1 channel, 24000 Hz, 16 bit).

**Fix:** branch on the format, fail on anything else:
- data starts with `RIFF` -> write the bytes as they are;
- mime contains `L16`/`pcm` -> wrap with the `rate=` from the mime type;
- otherwise raise.

**Disproven in the same session:** I first concluded the voice was slow (82-102 words/min). Wrong: every sample
started with my style instruction read aloud (see `2026-10-06-1345_gemini-tts-reads-instructions-aloud.md`). With
plain text the same voices run 116-160 words/min.
