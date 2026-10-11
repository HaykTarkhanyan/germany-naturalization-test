# Gemini TTS sometimes speaks a Russian line in another language; only the transcription check catches it

**Symptom:** Two Russian scenes came back in the wrong language, with no error from the API:
- Video 02, scene 4: "Канцлера объединения, Kanzler der Deutschen Einheit, зовут Helmut Kohl" was spoken (and
  transcribed twice in a row) as "Kanzler der Einheit, Kanzler der Deutschen Einheit, heißt Helmut Kohl": the
  German phrase in the middle pulled the whole first sentence into German. It passed the first, laxer check at
  exactly 70%.
- Video 04, scene 1: a plain Russian sentence was transcribed as Ukrainian ("На виборах в Бундестаг у вас два
  голоси, і важніше другий. 11 питань іспиту..."), overlap 39%. The same text came out as correct Russian on the
  next generation.
- Video 08, scene 5 ("Выборы в Германии свободные, равные и тайные: frei, gleich, geheim ..."): Ukrainian three
  attempts in a row ("Вибори в Німеччині — вільні, рівні і таємні").

**Cause:** Gemini 3.8 Flash TTS (Vertex, voice Charon, `speech_metadata` style) picks the spoken language per
generation when the request does not set `language_code` (ours did not). German words inside Russian text make a switch more likely, and plain
Russian can still drift (twice in about 200 scenes, one of them every time).

**What pins the language (tested on that scene, 2026-10-12):** `SpeechConfig(language_code="ru")` still gave
Ukrainian (overlap 22%); `language_code="ru-RU"` gave Russian (overlap 96%). The transcriber was the same in both
runs, so the voice really drifted. Russian clips now always use "ru-RU"; English has not drifted and stays unpinned.

**Fix:**
- Every clip is transcribed (`gemini-3.1-flash-lite`) and compared with the script; Russian is scored on Cyrillic
  words only (German names come back in arbitrary spelling) and must reach 80% (all correct scenes so far scored
  83% or more; the German-switched one 70%, the Ukrainian one 39%).
- A failing clip is kept as `sN.failedK.wav`, logged with its cost, and regenerated, up to 3 attempts; then the
  render stops.
- Scripts keep long German phrases out of Russian narration (they go on the on-screen card) and put a German term
  after the Russian sentence, not in its middle.

**Consequences:** never trust TTS output by its length or by a successful API response; check what was said.
