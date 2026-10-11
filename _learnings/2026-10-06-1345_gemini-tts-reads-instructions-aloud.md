# Gemini 3.8 Flash TTS reads its whole input aloud: style goes in speech_metadata, and every clip gets a transcription check

**Symptom:** Hayk listened to the first voice samples and the first demo video: every clip began with "Read aloud at a
natural, lively conversational pace..." (or "...calm, clear and friendly teacher's voice"), spoken by the voice.
I had not listened to or checked the audio content myself, only its duration, and built two wrong conclusions on
it (the voice is slow; speed the video up 1.2x).

**Cause:** Older Gemini TTS examples put the style in the text ("Say cheerfully: ..."). The 3.8 TTS models treat
the input as a verbatim transcript (ai.google.dev/gemini-api/docs/speech-generation). Passing the style as a
system instruction fails: `400 INVALID_ARGUMENT: Developer instruction is not enabled for this model`.

**Fix:** the Interactions API with the style as an annotation on the text (google-genai >= 2.25; 2.28.0 used):

```python
client.interactions.create(model="gemini-3.8-flash-tts",
    input=[{"type": "user_input", "content": [{"type": "text", "text": text,
            "annotations": [{"type": "speech_metadata", "style": "calm, clear and friendly teacher's voice"}]}]}],
    response_format={"type": "audio"}, generation_config={"speech_config": [{"voice": "Charon"}]})
# audio: base64.b64decode(interaction.output_audio.data), a complete WAV (24 kHz mono 16-bit)
```

**Evidence (2026-10-06, Charon, the 01_bayern opening line):**

| Input | Russian | English | Transcript vs text |
|---|---|---|---|
| instruction prefix + text (wrong) | 18.0-19.2 s | 16.3-16.4 s | instruction spoken |
| plain text | 10.0 s, 157 wpm | 11.2 s, 150 wpm | 100% words, +0 extra |
| text + speech_metadata style "calm..." | 15.1 s, 103 wpm | 12.8 s, 131 wpm | 100% words, +0 extra |

**Consequences:** every generated clip is now transcribed with `gemini-3.1-flash-lite` (about $0.00015 per scene)
and compared with the script; the run fails loudly if extra words are spoken (> max(3, 15%)) or fewer than 70% of
the script's words are heard. Generated media is verified by its content, not just its size or length.
