# Explainer videos (Russian and English) - plan

Status 2026-10-12: all 24 topics scripted as 14 videos, rendered in Russian and English (28 MP4s in
`videos/mp4/`, committed: DECISIONS #20). Voice: Gemini 3.8 Flash TTS, Charon, calm style, on Vertex (DECISIONS
#16-#17); every clip checked by transcription and regenerated on a mismatch. The renderer still lives outside the
repo (DEFERRED_TODO.md). The rest of this file is the plan as it was decided step by step.

Contents: [Goal](#goal) · [Format](#format) · [Two languages](#two-languages) · [Exam cards](#exam-cards) ·
[Which topics first](#which-topics-first) · [Scripts](#scripts) · [Pipeline](#pipeline) ·
[Decisions needed](#decisions-needed) · [Cost](#cost) · [Compute](#compute) · [Milestones](#milestones) ·
[Risks](#risks)

## Goal

Short videos that teach the facts worth memorizing, topic by topic, so studying can happen by watching
(commute, phone) instead of reading. Same rule as the lessons: minimal time. A video covers only the
**memorize** questions of its topic (data/lessons.json, DECISIONS.md #13); common-sense questions get one line
each in the recap.

## Format

- **Length:** about 2:00-2:40 per video with the chosen voice (Charon, calm style: measured 103 words/min in
  Russian and 131 in English on 2026-10-06), plus at least 3 s per exam card. Not sped up: the calm delivery is the
  one Hayk picked. (A first measurement of 82-102 words/min was wrong: my style instruction was being read aloud,
  `_learnings/2026-10-06-1345_*`.)
- **German terms** (Bundestag, Landtag, Fraktion) are spoken and shown in German in both versions, because the
  exam sheet is German; the narration explains them.
- **On screen:** a big German term card per fact, the exam cards (next section), and burned-in subtitles in the
  version's language.
- **Visuals:** the exam question and its answer are the content (Hayk 2026-10-06: no need to work on web
  images). A plain dark background, the exam card, and the exam picture inside the card for picture questions.
  Photos stay optional for later.
- **End card:** the German answers of the video in one list, and "Learn -> <topic>" in the app.

## Two languages

Every video exists twice, `NN_<lesson>.ru.mp4` and `NN_<lesson>.en.mp4`, rendered from the same script: same
scenes, visuals, term cards and exam cards. Only the voice track and the subtitles differ, and each version is
timed by its own voice (the English one runs 6-21 s longer). If the TTS allows it, one narrator voice speaks both
languages, so the two versions sound like the same person.

## Exam cards

Whenever the narration gives the answer to an exam question, that question appears on screen as it is on the
exam sheet, with the correct answer marked:

- the German question and its four options in catalog order (A-D), plus the picture for picture questions;
- the correct option in green with a check mark; the others plain;
- for picture questions whose answer is "Bild N" or a number in the picture (301 coat of arms, 308 map, 130 ballot
  in the pilot), a green box around the right picture too. The box position is set once by hand per image in
  `videos/image_marks.json`;
- the English translation on the card too (Hayk 2026-10-06), in both the Russian and the English video: under the
  German question, and after each German option on the same line, in grey (from data/translations_en.json, options
  in catalog order). The German stays first and bold, so the card still looks like the sheet;
- the card text is generated from data/questions_bayern.json at render time, never typed into a script, so it
  cannot drift from the official catalog.

**When:** the scripts mark the moment with `{Q301}` inside the narration, right where the answer is said. The
card fades in there and stays at least 3 s; markers with no words between them (the six "which state was in the
GDR" questions) come up together as a grid of small cards. Every question of the video's topic gets exactly one
card, including the common-sense ones in the recap. A fact from another topic mentioned only as a contrast
("the Bundestag: four years" in the Bayern video) gets no card; it has its own card in its own video.

## Which topics first

All 24 topics are scripted as 14 videos (2026-10-11). The first six were the pilot (one topic each, ranked by
memorize points: 7.7 of the catalog's 18.2). For the rest Hayk asked for longer videos with bigger groups where it
makes sense, so related topics share a video. Every one of the 310 questions has its exam card in exactly one video.

| # | Video | Lessons | Questions | RU / EN length |
|---|---|---|---|---|
| 01 | Bayern | bayern | 10 | 2:31 / 2:14 |
| 02 | Mauer und Einheit | mauer_einheit | 20 | 2:29 / 2:15 |
| 03 | Nachkriegszeit | nachkriegszeit | 16 | 2:15 / 2:02 |
| 04 | Bundestagswahl in der Praxis | wahlen_praxis | 15 | 2:12 / 2:09 |
| 05 | Kanzler und Präsident | regierung_praesident | 14 | 1:58 / 2:04 |
| 06 | Bundestag und Bundesrat | parlament | 14 | 1:48 / 1:49 |
| 07 | Grundgesetz, Grundrechte, Rechtsstaat | grundgesetz_grundrechte, demokratie_rechtsstaat, gleichbehandlung | 37 | 5:18 / 5:02 |
| 08 | Wahlen und Parteien | wahlen_grundsaetze, parteien | 24 | 3:53 / 3:50 |
| 09 | Bund, Länder, Gemeinden und Gerichte | foederalismus, gerichte_recht | 26 | 3:19 / 3:11 |
| 10 | Sozialstaat und Arbeit | sozialstaat_wirtschaft, arbeit | 22 | 3:13 / 2:59 |
| 11 | NS-Zeit, Krieg und Erinnerung | nationalsozialismus, juedisches_leben | 27 | 3:34 / 3:20 |
| 12 | Die DDR | ddr (02 and 03 already cover the neighbouring topics) | 13 | 2:11 / 2:05 |
| 13 | Deutschland und Europa | symbole_land, europa | 27 | 3:23 / 3:11 |
| 14 | Alltag: Familie, Schule, Religion, Behörden | familie, schule_bildung, religion_feste, alltag_behoerden | 45 | 5:30 / 5:22 |

Total: about 44 minutes in Russian and 42 in English (lengths estimated from the scripts at the measured pace:
103 words/min Russian, 131 English, at least 3 s per exam card). In the grouped videos the common-sense questions
get their cards in the scene they belong to, not only in the recap.

## Scripts

`videos/scripts/NN_<lesson>.md`, one per video, Markdown so they are easy to read and edit, with a fixed shape
so the pipeline can parse them:

```
## <n>. <scene title> (~<seconds> s)
- **Voice RU:** <Russian narration with {Q<id>} markers>
- **Voice EN:** <English narration with the same markers>
- **On screen:** <German term card>
- **Visual:** exam:<id> | commons:"<search>" | pexels:"<search>" | card
- **Questions:** <ids whose cards appear in this scene>
```

Rules: facts come only from data/lessons.json (already fact-checked twice, see `_learnings/`); every script also
says which believable wrong option to avoid; plain hyphens instead of dashes; German terms in Latin letters in
both narrations (the pilot decides whether the Russian voice needs a Cyrillic pronunciation hint, kept in one
`videos/pronunciation.json` if so). A check (run 2026-10-05, all six pass) confirms per script: both voices
carry the same markers as the Questions line, every topic question has exactly one card per language, and no
memorize question is left to the recap.

## Pipeline

**As built (2026-10-12):** `videos/pipeline/render.py` (DECISIONS #22). Steps 1, 2, 4 and 6 below without word
timings, `.srt` or a per-video JSON; no stock media (step 3 dropped on 2026-10-06), plain background, static frames.
Cached voice in `videos/build/render/<video>.<lang>/`, output straight into `videos/mp4/`. The plan as written:

All local, scripted, rerunnable; outputs in `videos/build/` (gitignored: audio, downloaded media, renders).

1. **Parse** a script into scenes; validate it (the check above).
2. **Voice:** TTS per scene and language, markers removed from the text -> audio file + duration + word timings
   (from the engine when it gives them; otherwise estimated from the marker's position in the text).
3. **Media:** fetch each scene's visual (exam image from data/images, Commons by search, Pexels by search), cache
   it with its source URL in `videos/build/media/sources.json` so a rebuild needs no new downloads. Shared by
   both languages.
4. **Cards:** render term cards and exam cards (from data/questions_bayern.json + image_marks.json) as images;
   build subtitles per language from the narration and its timings.
5. **Compose** per language: per scene, visual (clip trimmed to the narration, or a photo with a slow zoom) +
   term card + exam cards at their markers + narration; concatenate; burn in subtitles.
6. **Output:** `NN_<lesson>.<lang>.mp4` + `.srt`, plus `videos/build/<NN>.<lang>.json` with what went in
   (voice, media, durations).

## Decisions needed

### D1. Voice (TTS) - decided 2026-10-06: Gemini 3.8 Flash TTS, voice Charon, calm style

Prices checked 2026-10-05 on the official pricing pages (ElevenLabs, Azure) or the vendor's per-minute figure
(OpenAI). Size of the pilot, measured from the scripts: 9.7k Russian + 10.0k English narration characters,
about 20k per pass and ~40k with every scene voiced twice.

| Option | Russian / English quality | German terms inside the narration | Same voice in both languages | Pilot cost (~40k characters) |
|---|---|---|---|---|
| **ElevenLabs** (Multilingual v2 / v3) | Most natural and expressive in both | Multilingual model switches language inside one text; to test | Yes, one voice speaks both | Free plan 10k/month covers one language once; Starter $6/month for 30k (first month $1 until Oct 18); Creator $22 for 121k (first month $11) |
| **Azure Speech** (ru-RU: Dmitry, Svetlana, Dariya; many en-US/en-GB voices) | Very good, a bit "newsreader" | SSML fixes pronunciation and stress word by word | Separate voices per language (or a multilingual voice, to test) | 0.5M characters free per month, then $15 per 1M: $0 |
| **OpenAI gpt-4o-mini-tts** | Good English; Russian sometimes with an English-ish accent | Reads Latin German words, quality unknown | Yes | about $0.015 per minute: ~$0.62 for ~41 min of audio (20.6 min per pass, measured from the scripts) |
| **Gemini 3.8 Flash TTS** (Google AI Studio, key in `.env`; **tested 2026-10-06**, samples in `videos/build/voice_test/`) | Hayk to judge by ear; voices Charon and Kore tried | Same text with "Freistaat Bayern" in both languages; to judge | Yes, prebuilt voices speak both | Free tier $0; paid $0.50 per 1M text tokens + $9 per 1M audio tokens (25 tokens per second) through 2026-12-31: about $0.90 for the whole pilot with retakes (~68 min of audio at the measured pace) |
| **Local, no key** (Silero v5 for Russian; a separate open model for English, e.g. Kokoro) | Good Russian (automatic stress); English to test | Latin words need a hint | No, two different engines | $0, runs on the CPU in seconds |

**Decided (Hayk, 2026-10-06): Gemini 3.8 Flash TTS with Charon** in the "calm, clear and friendly teacher's
voice" style, passed as `speech_metadata` on the text part (never in the text itself: the model reads its input verbatim), called through Vertex AI (DECISIONS #17). Every clip is
checked by transcription before use. The rest of this section is the comparison that led here.

Earlier recommendation: **ElevenLabs**, because engagement matters for videos you are supposed to actually watch, one narrator
can speak both versions, and it is the most likely to pronounce German terms well inside Russian and English
sentences. The first milestone makes this cheap to check: the same 2 scenes in both languages with ElevenLabs
(free plan) and the local engines side by side; you choose by ear. **What would flip it:** if Azure or the local
voices sound close enough, take them (free, and SSML gives Azure exact control over German words); if ElevenLabs
mangles German terms, Azure. **Hard to reverse:** the voice. Switching later means re-voicing every video, so
pick it on the test.

### D2. Video assembly

| Option | Pros | Cons |
|---|---|---|
| **Python + ffmpeg** (ffmpeg 5.1.2 is already installed; cards drawn with Pillow) | No new framework, fast renders, deterministic, fits the repo's Python tooling (uv) | Animations are basic (fades, slow zoom, slide-in cards) |
| **Remotion** (React to video; free license for individuals) | Same React/TypeScript as the app, polished animated cards and maps; the app's question card could be reused | Heavier: renders with headless Chrome (more CPU, slower), more setup |
| **MoviePy 2.2** (Python wrapper around ffmpeg; maintained, last release Feb 2026) | Simpler compositing code than raw ffmpeg | Slower renders; v2 broke the v1 API, so most examples online are outdated |

**My pick: Python + ffmpeg** for the pilot: fastest to a first watchable video and light on the laptop.
**What would flip it:** if the pilot looks too plain, Remotion is the upgrade (the scripts stay the same, only
the renderer changes, so this is easy to reverse).

### D3. Shape

16:9 landscape (PC and YouTube; on a phone you rotate) or 9:16 portrait (phone first, like Shorts).
**My pick: 16:9**, because the exam pictures and the four-option exam cards are wide. Easy to reverse per video
(re-render).

### D4. Where the videos live

- local MP4 files only (simplest; you copy them to the phone),
- YouTube unlisted + a "Watch (2 min)" link in each lesson of the app, per language,
- GitHub Release assets of this repo (public download links, nothing in git history).

Not in the repo itself: 12 videos at 1080p are roughly 200-400 MB (guess), and GitHub Pages deploys the repo.
**My pick: local first**, decide on sharing after the pilot.
**Decided 2026-10-12:** committed to git in `videos/mp4/` (DECISIONS #20).

### D5. Keys

- Gemini: through **Vertex AI with the metric account** (application-default credentials; the Vertex project and
  location are in the gitignored `.env`), so calls bill the account with the trial credit (DECISIONS #17). The AI
  Studio key also in `.env` is no longer used;
- Pexels: not needed now (no stock video, see Visuals).

## Cost

Whole pilot (6 videos x 2 languages, every scene voiced twice): **$0-11** depending on D1 (Azure and the local
engines $0, OpenAI under $1, ElevenLabs $6 or $11 for the first month). Media: $0 (Pexels and Commons are free). I
will show the estimate again before the first paid call and report actual spend afterwards (cost ledger in
`videos/build/costs.json`).

## Compute

Rendering a 2 minute 1080p video with ffmpeg uses all CPU cores for roughly 1-3 minutes (guess, to be measured on
the first render); the pilot is 12 renders. Per the house rules I will ask before the first render and render one
video at a time, in the background, with a 720p preview first.

## Milestones

1. **Voice test**: done 2026-10-06, see `videos/build/index.html` (Charon picked).
2. **Pilot video 01_bayern** in Russian and English: demo rendered 2026-10-06 with static frames
   (`videos/build/demo/`); Hayk watches and gives notes.
3. **Batch 02-06** with the pilot's fixes, one at a time.
4. Optional: links from the app's lessons (if D4 = YouTube or Release assets).

## Risks

- **German terms mispronounced or wrong stress** in the TTS: test in milestone 1; fallback is a pronunciation hint
  per term in `videos/pronunciation.json`, or Azure SSML.
- **Cards too fast to read:** 3 s minimum per card is a guess; the pilot shows whether the scene needs a pause
  after a card.
- **Generic stock footage** (a random Berlin street for "Bundesrat"): prefer the exam picture and Commons photos
  of the real building/person; stock only as background.
- **Accuracy:** the narration restates data/lessons.json only; no new claims. Facts that can change (chancellor,
  president, EU members) are dated in the script.
- **A fact that is right but primes a wrong option** (learned in the lesson review, `_learnings/2026-10-05-1545_*`):
  every script also says which believable wrong option to avoid.
